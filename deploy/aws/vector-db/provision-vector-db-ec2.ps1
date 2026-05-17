param(
    [string]$Region = $(if ($env:AWS_REGION) { $env:AWS_REGION } else { "us-east-1" }),
    [string]$Profile = $env:AWS_PROFILE,
    [string]$InstanceName = "support-vector-db",
    [string]$InstanceType = "t3.micro",
    [string]$AmiId = "",
    [int]$RootVolumeSizeGb = 20,
    [string]$PostgresUser = $(if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "admin" }),
    [string]$PostgresPassword = $env:POSTGRES_PASSWORD,
    [string]$PostgresDb = $(if ($env:POSTGRES_DB) { $env:POSTGRES_DB } else { "vectordb" }),
    [string]$VpcIngressCidr = "",
    [string]$PublicIngressCidr = ""
)

$ErrorActionPreference = "Stop"

$ScriptRoot = $PSScriptRoot
$AwsCmd = $env:AWS_CMD
if (-not $AwsCmd) {
    $candidate = Join-Path $env:APPDATA "Python\Python314\Scripts\aws.cmd"
    if (Test-Path $candidate) {
        $AwsCmd = $candidate
    } else {
        $cmd = Get-Command aws -ErrorAction SilentlyContinue
        if ($cmd) { $AwsCmd = $cmd.Source }
    }
}
if (-not $AwsCmd) {
    throw "AWS CLI was not found. Set AWS_CMD or install/configure AWS CLI."
}

$BaseAwsArgs = @("--region", $Region)
if ($Profile) {
    $BaseAwsArgs += @("--profile", $Profile)
}

function Invoke-Aws {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        $env:PYTHONIOENCODING = "utf-8"
        $output = & $AwsCmd @BaseAwsArgs @Args 2>&1
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($exitCode -ne 0) {
        throw "aws command failed: aws $($BaseAwsArgs -join ' ') $($Args -join ' ')`n$($output -join [Environment]::NewLine)"
    }
    $output
}

if (-not $PostgresPassword) {
    $PostgresPassword = [Guid]::NewGuid().ToString("N")
}

if (-not $AmiId) {
    try {
        $AmiId = Invoke-Aws ssm get-parameter `
            --name "/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id" `
            --query "Parameter.Value" `
            --output text
    } catch {
        Write-Warning "Could not read the Ubuntu AMI SSM parameter. Falling back to EC2 describe-images."
        $AmiId = Invoke-Aws ec2 describe-images `
            --owners 099720109477 `
            --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" "Name=architecture,Values=x86_64" "Name=virtualization-type,Values=hvm" `
            --query "sort_by(Images, &CreationDate)[-1].ImageId" `
            --output text
    }
}

$RootDeviceName = Invoke-Aws ec2 describe-images `
    --image-ids $AmiId `
    --query "Images[0].RootDeviceName" `
    --output text

$VpcInfo = Invoke-Aws ec2 describe-vpcs `
    --filters "Name=is-default,Values=true" `
    --query "Vpcs[0].{VpcId:VpcId,CidrBlock:CidrBlock}" `
    --output json | ConvertFrom-Json

if (-not $VpcInfo -or -not $VpcInfo.VpcId) {
    throw "No default VPC found in region $Region."
}
if (-not $VpcIngressCidr) {
    $VpcIngressCidr = $VpcInfo.CidrBlock
}

$SubnetId = Invoke-Aws ec2 describe-subnets `
    --filters "Name=vpc-id,Values=$($VpcInfo.VpcId)" `
    --query "Subnets[0].SubnetId" `
    --output text

$SgName = "$InstanceName-sg"
$SecurityGroupId = $null
try {
    $SecurityGroupId = Invoke-Aws ec2 describe-security-groups `
        --filters "Name=group-name,Values=$SgName" "Name=vpc-id,Values=$($VpcInfo.VpcId)" `
        --query "SecurityGroups[0].GroupId" `
        --output text
} catch {}
if (-not $SecurityGroupId -or $SecurityGroupId -eq "None") {
    $SecurityGroupId = Invoke-Aws ec2 create-security-group `
        --group-name $SgName `
        --description "Support Copilot pgvector and ChromaDB access" `
        --vpc-id $VpcInfo.VpcId `
        --query "GroupId" `
        --output text
}

$IngressCidrs = @($VpcIngressCidr)
if ($PublicIngressCidr) {
    $publicCidrs = @(
        $PublicIngressCidr -split "," |
            ForEach-Object { $_.Trim() } |
            Where-Object { $_ }
    )
    if ($publicCidrs -contains "0.0.0.0/0") {
        Write-Warning "PublicIngressCidr includes 0.0.0.0/0. This exposes Postgres and ChromaDB to the public internet. Prefer the client cloud outbound IP as x.x.x.x/32."
    }
    $IngressCidrs += $publicCidrs
}

foreach ($cidr in $IngressCidrs) {
    foreach ($port in @("5432", "8000")) {
        try {
            Invoke-Aws ec2 authorize-security-group-ingress `
                --group-id $SecurityGroupId `
                --protocol tcp `
                --port $port `
                --cidr $cidr | Out-Null
        } catch {
            if ($_.Exception.Message -notmatch "InvalidPermission.Duplicate") { throw }
        }
    }
}

$Compose = Get-Content -Raw -Path (Join-Path $ScriptRoot "docker-compose.yml")
$UserData = Get-Content -Raw -Path (Join-Path $ScriptRoot "user-data.sh")
$UserData = $UserData.Replace("__POSTGRES_USER__", $PostgresUser)
$UserData = $UserData.Replace("__POSTGRES_PASSWORD__", $PostgresPassword)
$UserData = $UserData.Replace("__POSTGRES_DB__", $PostgresDb)
$UserData = $UserData.Replace("__DOCKER_COMPOSE__", $Compose.Trim())

$WorkDir = Join-Path $env:TEMP ("support-vector-db-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $WorkDir | Out-Null
$UserDataPath = Join-Path $WorkDir "user-data.sh"
Set-Content -Path $UserDataPath -Value $UserData -NoNewline

try {
    $InstanceId = Invoke-Aws ec2 run-instances `
        --image-id $AmiId `
        --instance-type $InstanceType `
        --security-group-ids $SecurityGroupId `
        --subnet-id $SubnetId `
        --associate-public-ip-address `
        --block-device-mappings "DeviceName=$RootDeviceName,Ebs={VolumeSize=$RootVolumeSizeGb,VolumeType=gp3,DeleteOnTermination=true}" `
        --user-data "file://$UserDataPath" `
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$InstanceName}]" `
        --query "Instances[0].InstanceId" `
        --output text

    Write-Host "Waiting for instance $InstanceId..."
    Invoke-Aws ec2 wait instance-running --instance-ids $InstanceId

    $Instance = Invoke-Aws ec2 describe-instances `
        --instance-ids $InstanceId `
        --query "Reservations[0].Instances[0].{PublicIp:PublicIpAddress,PrivateIp:PrivateIpAddress}" `
        --output json | ConvertFrom-Json

    Write-Host ""
    Write-Host "Vector DB EC2 instance is running."
    Write-Host "InstanceId:      $InstanceId"
    Write-Host "PublicIp:        $($Instance.PublicIp)"
    Write-Host "PrivateIp:       $($Instance.PrivateIp)"
    Write-Host "Postgres user:   $PostgresUser"
    Write-Host "Postgres db:     $PostgresDb"
    Write-Host "Postgres pass:   $PostgresPassword"
    Write-Host ""
    Write-Host "Use these from AWS apps in the same VPC:"
    Write-Host "DATABASE_URL=postgresql+asyncpg://$PostgresUser`:$PostgresPassword@$($Instance.PrivateIp):5432/$PostgresDb"
    Write-Host "CHROMA_HOST=$($Instance.PrivateIp)"
    Write-Host "CHROMA_PORT=8000"
    Write-Host "CHROMA_URL=http://$($Instance.PrivateIp):8000"
    if ($PublicIngressCidr) {
        Write-Host ""
        Write-Host "Use these from the allowed external client cloud CIDR(s):"
        Write-Host "DATABASE_URL=postgresql+asyncpg://$PostgresUser`:$PostgresPassword@$($Instance.PublicIp):5432/$PostgresDb"
        Write-Host "CHROMA_HOST=$($Instance.PublicIp)"
        Write-Host "CHROMA_PORT=8000"
        Write-Host "CHROMA_URL=http://$($Instance.PublicIp):8000"
    }
    Write-Host ""
    Write-Host "Deployment continues in EC2 cloud-init. Check console output if it is not ready after 5-10 minutes."
} finally {
    Remove-Item -Recurse -Force $WorkDir -ErrorAction SilentlyContinue
}
