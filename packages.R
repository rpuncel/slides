# Install required R packages for this project
install.packages("plotly")
install.packages("tidyverse")
install.packages("lazyeval")
install.packages("commonmark")

# Snapshot the current state of the library
renv::snapshot()
