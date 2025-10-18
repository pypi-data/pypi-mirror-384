#!/usr/bin/env Rscript

# Set seed
set.seed(1234)

# List of required packages
# Note that imputeLCMD is loaded lazily to avoid loading the entire namespace
packages <- c("arrow", "optparse")

# Load packages quietly
print(paste0(Sys.time(), ": ", "Loading required R packages..."))
invisible(lapply(packages, FUN = function(pkg)
{suppressWarnings(suppressMessages(library(pkg, character.only = TRUE, quietly = T)))}
))

# Define expected arguments
option_list = list(
  make_option(c("--out"), type="character")
)

# Parse received arguments
print(paste0(Sys.time(), ": ", "Parsing arguments..."))
opt = parse_args(OptionParser(option_list=option_list, add_help_option=F))
print(opt)

# Load imputeLCMD example dataset PXD000438
# http://proteomecentral.proteomexchange.org/cgi/GetDataset?ID=PXD000438
print(paste0(Sys.time(), ": ", "Loading dataset PXD000438..."))
data(intensity_PXD000438, package = "imputeLCMD")

# Write results to temp feather file
print(paste0(Sys.time(), ": ", "Writing results..."))
write_feather(intensity_PXD000438, sink = opt$out)

print(paste0(Sys.time(), ": ", "Closing..."))
print("----Session info----")
sessionInfo()
