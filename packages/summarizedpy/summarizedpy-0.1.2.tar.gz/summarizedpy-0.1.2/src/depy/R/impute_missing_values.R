#!/usr/bin/env Rscript
env_path <- grep("/envs/depy", .libPaths())

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
  make_option(c("--expr"), type="character"),
  make_option(c("--out"), type="character"),
  make_option(c("--method"), type="character"),
  make_option(c("--q"), type="integer"),
  make_option(c("--k"), type="integer"),
  make_option(c("--tune_sigma"), type="integer"),
  make_option(c("--mar"), type="character"),
  make_option(c("--mnar"), type="character")
  )

# Parse received arguments
print(paste0(Sys.time(), ": ", "Parsing arguments..."))
opt = parse_args(OptionParser(option_list=option_list, add_help_option=F))
print(opt)

# Read in data matrix from temp feather file
print(paste0(Sys.time(), ": ", "Reading feature matrix..."))
feature_matrix <- read_feather(opt$expr)
feature_matrix <- as.matrix(feature_matrix)

# Missing value imputation using ImputeLCMD package
# Defaults below sourced from ImputeLCMD source code: https://github.com/cran/imputeLCMD/blob/master/R
print(paste0(Sys.time(), ": ", "Running imputation..."))
imputation <- function(mat=NULL, method=NULL, K=NULL, q=NULL, tune.sigma=NULL, MAR=NULL, MNAR=NULL) {
  
  if (method == "KNN") {
    if (is.null(K)) {
      K<-15
      print(paste0("Running KNN with default K=", K))
      }
    mat <- imputeLCMD::impute.wrapper.KNN(mat, K=K)}
  if (method == "MLE") {mat <- imputeLCMD::impute.wrapper.MLE(mat)}
  if (method == "SVD") {
    if (is.null(K)) {
      K<-2
      print(paste0("Running SVD with default K=", K))
      }
    mat <- imputeLCMD::impute.wrapper.SVD(mat, K=K)}
  if (method == "QRILC") {
    if (is.null(tune.sigma)) {
      tune.sigma<-1
      print(paste0("Running QRILC with default tune.sigma=", tune.sigma))
      }
    mat <- imputeLCMD::impute.QRILC(mat, tune.sigma=tune.sigma)[1]}
  if (method == "MinDet") {
    if (is.null(q)) {
      q<-0.01
      print(paste0("Running MinDet with default q=", q))
      }
    mat <- imputeLCMD::impute.MinDet(mat, q=q)}
  if (method == "MinProb") {
    if (is.null(q)) {
      q<-0.01
      print(paste0("Running MinProb with default q=", q))
      }
    if (is.null(tune.sigma)) {
      tune.sigma<-1
      print(paste0("Running MinProb with default tune.sigma=", tune.sigma))
      }
    mat <- imputeLCMD::impute.MinProb(mat, q=q, tune.sigma=tune.sigma)}
  if (method == "Hybrid") {
    if (is.null(MAR)) {
      MAR<-"KNN"
      print(paste0("Running Hybrid with default MAR=", MAR))
      
    }
    if (is.null(MNAR)) {
      MNAR<-"QRILC"
      print(paste0("Running Hybrid with default MNAR=", MNAR))
    }
      
    mat <- imputeLCMD::impute.MAR.MNAR(
    dataSet.mvs = mat, 
    model.selector = imputeLCMD::model.Selector(mat), 
    method.MAR = MAR, 
    method.MNAR = MNAR)}
  return(mat)
  
}

# Run imputation
feature_matrix <- imputation(mat=feature_matrix, 
                             method=opt$method, 
                             K=opt$k, 
                             q=opt$q, 
                             tune.sigma=opt$tune_sigm, 
                             MAR=opt$mar, 
                             MNAR=opt$mnar)
feature_matrix <- as.data.frame(feature_matrix)

# Write results to temp feather file
print(paste0(Sys.time(), ": ", "Writing results..."))
write_feather(feature_matrix, sink = opt$out)

print(paste0(Sys.time(), ": ", "Closing..."))
print("----Session info----")
sessionInfo()

