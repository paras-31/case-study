

variable "files" {
  default = 5
}

resource "local_file" "foo" {
  count    = var.files
  content  = "# Some content for file ${count.index}"
  filename = "file${count.index}.txt"
}