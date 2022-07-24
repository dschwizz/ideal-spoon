library(data.table)
library(parallel)
library(cluster)
library(clusterCrit)
library(TSrepr)
library(ggplot2)
library(grid)
library(tidyverse)
# import randomly generated sku level demand
time_series_demand <- read_csv("time series demand.csv")
df <- time_series_demand

# normalize sales data
df$normSales <- (df$`Sales Units`-mean(df$`Sales Units`))/sd(df$`Sales Units`)

# scale data by largest sales value
df$scale <- df$`Sales Units`/max(df$`Sales Units`)

# reshape column data into a matrix
df<- df %>% 
  select(period = FiscalPeriodOfYearNum, style = StyleNumber, units = `Sales Units`) %>%
  spread(key = period, value = units)
df_mat <- data.matrix(df)

# set number of periods to 13
period = 13

# run clustering algorithm on the matrix (15 clusters)
res_clust <- kmeans(df_mat[,2:14], 15, nstart = 20)

# unpivt the matrix and match the clusters to the skus
data_plot <- data.table(melt(df_mat[,2:14]))
data_plot[, Clust := rep(res_clust$cluster, ncol(df_mat[,2:14]))]

# pull out the centroid for each cluster
data_centroid <- data.table(melt(res_clust$centers))
data_centroid[, Clust := Var1]

# plot the actuals and the centroids together to visualize the clusters
ggplot(data_plot) +
  facet_wrap(~Clust, scales = "free", ncol = 3) +
  geom_line(aes(Var2, value, group = Var1), alpha = 0.7) +
  geom_line(data = data_centroid, aes(Var2, value, group = Var1),
            alpha = 0.8, color = "red", size = 1.2) +
  scale_x_continuous(breaks = seq(1, 13, 1),
                     labels = paste("P",seq(1, 13, by = 1), sep = ""))