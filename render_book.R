args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)

if (length(file_arg) == 1) {
  script_path <- normalizePath(sub("^--file=", "", file_arg), mustWork = TRUE)
  project_dir <- dirname(script_path)
} else {
  project_dir <- normalizePath("iobrpy-bookdown", mustWork = TRUE)
}

local_library <- file.path(project_dir, ".r-library")
if (dir.exists(local_library)) {
  inherited_libraries <- .libPaths()
  Sys.setenv(
    R_LIBS_USER = paste(
      unique(c(local_library, inherited_libraries)),
      collapse = .Platform$path.sep
    )
  )
  .libPaths(c(local_library, inherited_libraries))
}

required <- c("bookdown", "rmarkdown", "knitr")
missing <- required[
  !vapply(required, requireNamespace, logical(1), quietly = TRUE)
]

if (length(missing) > 0) {
  stop(
    "Missing R packages: ",
    paste(missing, collapse = ", "),
    ". Install them before rendering."
  )
}

output_dir <- file.path(project_dir, "_book")
if (dir.exists(output_dir)) {
  unlink(output_dir, recursive = TRUE, force = TRUE)
}

bookdown::render_book(
  input = project_dir,
  output_format = "bookdown::gitbook",
  clean = TRUE
)
