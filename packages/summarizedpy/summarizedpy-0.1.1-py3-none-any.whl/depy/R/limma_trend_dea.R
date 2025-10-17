#!/usr/bin/env Rscript

# Set seed
set.seed(1234)

# List of required packages
packages <- c("limma", "dplyr", "purrr", "stringr", "tibble", "tidyr", "arrow", "optparse")

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
  make_option(c("--features"), type="character"),
  make_option(c("--feature_id_col"), type="character"),
  make_option(c("--design_formula"), type="character"),
  make_option(c("--contrasts"), type="character"),
  make_option(c("--robust"), type="logical"),
  make_option(c("--block"), type="character"),
  make_option(c("--array_weights"), type="logical"),
  make_option(c("--prior_n"), type="integer"),
  make_option(c("--var_group"), type="character"),
  make_option(c("--sample_id_col"), type="character")
)

# Parse received arguments
print(paste0(Sys.time(), ": ", "Parsing arguments..."))
opt = parse_args(OptionParser(option_list=option_list, add_help_option=F))
print(opt)

# Read in data matrix from temp feather file
# Omit missing values as SVA will throw an error otherwise
print(paste0(Sys.time(), ": ", "Reading feature matrix..."))
feature_matrix <- as.matrix(read_feather(file = opt$expr))
colnames(feature_matrix) <- paste0("sample_", 1:ncol(feature_matrix))
rownames(feature_matrix) <- paste0("feature_", 1:nrow(feature_matrix))

# Read in sample metadata from temp feather file
print(paste0(Sys.time(), ": ", "Reading sample metadata..."))
samples <- read_feather(file = opt$samples)
stopifnot(ncol(feature_matrix) == nrow(samples))

# Read in features metadata from temp feather file
if (!is.null(opt$feature_id_col)) {
  
  print(paste0(Sys.time(), ": ", "Reading feature metadata..."))
  features <- read_feather(file = opt$features)
  stopifnot(nrow(feature_matrix) == nrow(features))
  rownames(feature_matrix) <- features %>% pull(opt$feature_id_col)
  
}

# Create limma model.matrix & tidy column names to match contrast definition
# The term.labels attribute is used as a regex to remove automatically appended strings in the column names
print(paste0(Sys.time(), ": ", "Creating design matrix..."))
design_formula <- as.formula(opt$design_formula)
design <- model.matrix(design_formula, data=samples)
colnames(design) <- str_remove_all(colnames(design), paste0(attr(terms(design_formula), "term.labels"), collapse = "|"))

# Parse contrasts string into named vector for limma's makeContrasts
# Formatting uses '@' to separate contrasts and ':' to separate contrast name (key) and definition (value)
print(paste0(Sys.time(), ": ", "Parsing contrasts..."))
contrasts <- opt$contrasts
contrasts <- unlist(str_split(contrasts, "@")) 
names(contrasts) <- unlist(str_split_i(contrasts, ":", i=1))
contrasts <- map(contrasts, ~str_extract(.x, "(?<=:)(.+)"))
contrasts <- unlist(contrasts)
contr.matrix <- makeContrasts(contrasts = contrasts, levels = design)
colnames(contr.matrix) <- names(contrasts)

# limma trend function 
print(paste0(Sys.time(), ": ", "Initializing limma-trend..."))
limma_trend_dea <- function(mat=NULL, des=NULL, c_mat=NULL, 
                            robust=NULL, 
                            arr_weights=NULL, 
                            block=NULL, 
                            prior.n=NULL, 
                            var.group=NULL, 
                            sample_id_col=NULL){
  
  correlation <- NULL
  weights <- NULL
  
  if (arr_weights) {
    
    if (is.null(prior.n)) {prior.n=10}
    if (!is.null(var.group)) {var.group <- samples %>% pull(var.group)}
    print(paste0(Sys.time(), ": ", "Calculating array weights..."))
    weights <- arrayWeights(mat, design=des, method="reml", prior.n=prior.n, var.group=var.group)
    
    names(weights) <- colnames(feature_matrix)
    if (!is.null(sample_id_col)) {names(weights) <- samples %>% pull(sample_id_col)}
    
    print("---Sample weights----")
    print(weights)
  }
  if (!is.null(block)) {
    block <- samples %>% pull(block)
    print(paste0(Sys.time(), ": ", "Calculating consensus correlation..."))
    corfit <- duplicateCorrelation(mat, design=des, block=block, weights=weights)
    correlation <- corfit$consensus.correlation
    print(paste0("Consensus correlation: ", correlation))
  }
  
  print(paste0(Sys.time(), ": ", "Fitting model..."))
  vfit <- lmFit(mat, 
                design=des, 
                block=block, 
                correlation=correlation,
                weights=weights)
  
  print(paste0(Sys.time(), ": ", "Fitting contrasts..."))
  vfit <- contrasts.fit(vfit, c_mat)
  
  print(paste0(Sys.time(), ": ", "Fitting eBayes trend..."))
  efit <- eBayes(vfit, trend = T, robust=robust)
  
  return(efit)
}
efit <- limma_trend_dea(mat=feature_matrix, 
                        des=design, 
                        c_mat=contr.matrix, 
                        robust=opt$robust, 
                        block=opt$block,
                        arr_weights=opt$array_weights,
                        prior.n=opt$prior_n,
                        var.group=opt$var_group,
                        sample_id_col=opt$sample_id_col)

# Extract DEA results into nested tibble
print(paste0(Sys.time(), ": ", "Extracting DEA results..."))
dea_results <- tibble(contrast_label = colnames(efit$contrasts),
                      results = map(contrast_label, 
                                    function(.x) 
                                      rownames_to_column(
                                        topTable(efit, 
                                                 coef = .x, 
                                                 number = Inf, 
                                                 sort.by = "p", 
                                                 confint = T), 
                                        var = "feature"))) %>%
  unnest(results)

# Add contrast_label and contrast definition variables to dea_results
dea_results <- tibble(contrast_label = names(contrasts),
                      contrast = contrasts) %>%
  inner_join(dea_results, by = "contrast_label")

# Write results to temp feather file
print(paste0(Sys.time(), ": ", "Writing results..."))
write_feather(dea_results, sink = opt$out)

print(paste0(Sys.time(), ": ", "Closing..."))
print("----Session info----")
sessionInfo()
