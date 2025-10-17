#!/usr/bin/env Rscript

# Set seed
set.seed(1234)

# List of required packages
# Note that sva is loaded lazily to avoid loading the entire namespace
packages <- c("arrow", "optparse")

# Load packages quietly
print(paste0(Sys.time(), ": ", "Loading required R packages..."))
invisible(lapply(packages, FUN = function(pkg)
{suppressWarnings(suppressMessages(library(pkg, character.only = TRUE, quietly = T)))}
))

# Define expected arguments
option_list = list(
  make_option(c("--expr"), type="character"),
  make_option(c("--out"), type="character"),
  make_option(c("--samples"), type="character"),
  make_option(c("--mod"), type="character"),
  make_option(c("--mod0"), type="character"),
  make_option(c("--num_sv"), type="integer"))

# Parse received arguments
print(paste0(Sys.time(), ": ", "Parsing arguments..."))
opt = parse_args(OptionParser(option_list=option_list, add_help_option=F))
print(opt)

# Read in data matrix from temp feather file
# Omit missing values as SVA will throw an error otherwise
print(paste0(Sys.time(), ": ", "Reading feature matrix..."))
feature_matrix <- read_feather(opt$expr)
feature_matrix <- na.omit(as.matrix(feature_matrix))

# Read in sample metadata from temp feather file
print(paste0(Sys.time(), ": ", "Reading sample metadata..."))
samples <- read_feather(opt$samples)
samples <- as.data.frame(samples)

# SVA
print(paste0(Sys.time(), ": ", "Preparing SVA arguments..."))
mod <- as.formula(opt$mod)
mod0 <- as.formula(opt$mod0)
num_sv <- opt$num_sv

# Model matrices
print(paste0(Sys.time(), ": ", "Preparing mod(0) matrices..."))
mod <- model.matrix(mod, data = samples)
mod0 <- model.matrix(mod0, data = samples)

# Estimate num.sv if num_sv was not supplied by user
if (is.null(num_sv)) {
  print(paste0(Sys.time(), ": ", "Estimating num.sv..."))
  num_sv <- sva::num.sv(feature_matrix, mod, method = "leek")
  stopifnot("The number of estimated SVs was 0"= num_sv > 0)
  }

# Run SVA
print(paste0(Sys.time(), ": ", "Running sva..."))
svobj = sva::sva(feature_matrix, mod=mod, mod0=mod0, n.sv=num_sv)

# Add SV to sample metadata
print(paste0(Sys.time(), ": ", "Adding SVs to samples metadata..."))
colnames(svobj$sv) <- paste0("sv_", 1:ncol(svobj$sv))
samples <- cbind(samples, svobj$sv)

# Write results to temp feather file
print(paste0(Sys.time(), ": ", "Writing results..."))
write_feather(samples, sink = opt$out)

print(paste0(Sys.time(), ": ", "Closing..."))
print("----Session info----")
sessionInfo()
