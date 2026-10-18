variable "name" { type = string }
variable "instance_type" { type = string }

data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-2023*-x86_64"]
  }
}

resource "aws_instance" "this" {
  ami           = data.aws_ami.al2023.id
  instance_type = var.instance_type

  metadata_options {
    http_tokens = "required" # IMDSv2 only
  }
  root_block_device {
    encrypted = true
  }
  tags = { Name = var.name }
}

output "instance_id" { value = aws_instance.this.id }
output "public_ip" { value = aws_instance.this.public_ip }
