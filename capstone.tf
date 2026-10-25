resource "local_file" "capstone_env" {
  filename = "${path.module}/capstone.env"
  content  = "PAYMENT_GATEWAY_URL=http://localhost:30099\nSTATUS=DEPLOYED\n"
}
