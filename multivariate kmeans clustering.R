library(cluster)
library(ggplot2)
library(plot3D)
library(dendextend)
library(ape)
library(readr)
library(dplyr)

##pull in data to test code
styleClustering <- read_csv("SKUdataforclustering.csv")
df <- as.data.frame(styleClustering)
df$gm_perc <- df$gm/df$retail
df$gm_perc[is.na(df$gm_perc)] <- mean(df$gm_perc, na.rm = TRUE)
df$gm <- df$retail*df$gm_perc


##choose variables and scale using the following: (actual - mean)/standard deviation
df <- df[,c('sku_id','units','retail', 'gm')]

df$units <- (df$units - mean(df$units))/sd(df$units)
df$retail <- (df$retail - mean(df$retail))/sd(df$retail)
df$gm <- (df$gm - mean(df$gm))/sd(df$gm)

#set seed number to ensure that each running of the clustering code returns the same results
set.seed(20)

##K-Means

##find optimal clusters
k.max<-15
wss<-sapply(1:k.max, function(k){kmeans(df[c(2:4)],k,nstart=50,iter.max = 15)$tot.withinss})
p1<-plot(1:k.max, wss,
         type="b", pch = 19, frame = FALSE, 
         xlab="Number of clusters K",
         ylab="Total within-clusters sum of squares")

##four clusters K-Means
start_time_kMeans4 <- Sys.time()
styleClusters<-kmeans(df[c(2:4)],4)
end_time_kMeans4 <- Sys.time()

df$kmeans_cluster <- styleClusters$cluster

##K-Mediods
## Use the silhouette widths for assessing the best number of clusters (best =  w/ avg.width = ; 5 clusters has avg.width = )
start_time1 <- Sys.time()
asw <- numeric(20)
for (k in 2:20)
  asw[k] <- pam(df[c(2:4)], k) $ silinfo $ avg.width
k.best <- which.max(asw)
end_time1 <- Sys.time()

##best clusters K-mediod
start_time_kMediods <- Sys.time()
styleClusters1<-pam(df[c(2:4)],k.best)
end_time_kMediods <- Sys.time()

df$kmediods_cluster_best <- styleClusters1$clustering


##four clusters K-mediod
start_time_kMediods4 <- Sys.time()
styleClusters2<-pam(df[c(2:4)],4)
end_time_kMediods4 <- Sys.time()

df$kmediods_cluster_3 <- styleClusters2$clustering


##3d Plot
x<-df$units
y<-df$retail
z<-df$gm

scatter3D(x, y, z, bty = "b2", pch = 19,
          colvar = styleClusters1$cluster,
          col = c("red","green"),
          colkey = list(length = 0.5, width = 0.5, side = 1),
          xlab = "Sales Units",
          zlab ="GM $",
          ylab = "Sales at Retail $")

###############################################################
# Hierarchical Clustering Methods

##Agglomerative Hierachical Clustering
start_time_aggHie <- Sys.time()
d <- dist(df, method = "euclidean")
style.hc <- hclust(d,method = "ward.D2")
clus4 = cutree(style.hc, 4) #cluster into 4 groups
end_time_aggHie <- Sys.time()


##Divise Hierachical Clustering
start_time_diana <- Sys.time()
diana <- diana(df)
style.diana <- as.dendrogram(diana)
style.diana %>% plot(main = "Divisive Hierachical Clustering") %>% rect.dendrogram(k=4)
end_time_diana <- Sys.time()

table(clus4) #number of Styles per group
rownames(df)[clus4==1]
rownames(df)[clus4==2]
rownames(df)[clus4==3]
rownames(df)[clus4==4]

##dendogram plots for HClustering

#cluster Dedogram
plot(style.hc, cex= 0.6, hang = -1)
rect.hclust(style.hc, k=4, border=2:5)

#unrooted Phylogenetic tree
plot(as.phylo(as.hclust(style.ag)), type = "unrooted", tip.color = colors[clus3],
     no.margin = TRUE, cex = 0.6, lab4ut = "axial", rotate.tree = 90, xlim)


#runtimes
run_time_1 <- end_time1 - start_time1
run_time_kMediods <- end_time_kMediods - start_time_kMediods
run_time_kmeans <- end_time_kMeans4 - start_time_kMeans4
run_time_kMediods4 <- end_time_kMediods4 - start_time_kMediods4 
run_time_aggHie <- end_time_aggHie - start_time_aggHie
run_time_diana <- end_time_diana - start_time_diana