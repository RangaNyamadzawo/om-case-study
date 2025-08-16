# Add steps/actions here:   

# 1. step 1
 Convert from count to for_each using stable keys, then remove only the key representing the “2nd” item.

    variable "file_keys" {
        default = ["0", "1", "2", "3", "4"] 
    }

    resource "local_file" "foo" {
        for_each = toset(var.file_keys)

        content  = "# Some content for file ${each.key}"
        filename = "file${each.key}.txt"
    }

