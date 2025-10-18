#!/usr/bin/env Rscript

# Set seed
set.seed(1234)

# List of required packages
# Note that vsn is loaded lazily to avoid loading the entire namespace
packages <- c("arrow", "optparse")

# Load packages quietly
print(paste0(Sys.time(), ": ", "Loading required R packages..."))
invisible(lapply(packages, FUN = function(pkg)
{suppressWarnings(suppressMessages(library(pkg, character.only = TRUE, quietly = T)))}
))

# Define expected arguments
option_list = list(
  make_option(c("--expr"), type="character"),
  make_option(c("--out"), type="character"))

# Parse received arguments
print(paste0(Sys.time(), ": ", "Parsing arguments..."))
opt = parse_args(OptionParser(option_list=option_list, add_help_option=F))
print(opt)

# Read in data matrix from temp feather file
print(paste0(Sys.time(), ": ", "Reading feature matrix..."))
feature_matrix <- read_feather(opt$expr)
feature_matrix <- as.matrix(feature_matrix)

# Feature Normalization using VSN with default outlier tolerance = 10%
print(paste0(Sys.time(), ": ", "Running vsn..."))
feature_matrix <- vsn::justvsn(feature_matrix, lts.quantile = 0.9)
feature_matrix <- as.data.frame(feature_matrix)

# Write results to temp feather file
print(paste0(Sys.time(), ": ", "Writing results..."))
write_feather(feature_matrix, sink = opt$out)

print(paste0(Sys.time(), ": ", "Closing..."))
print("----Session info----")
sessionInfo()
