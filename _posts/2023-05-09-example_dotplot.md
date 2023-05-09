---
title: 'Visualize your Experimental Results with a dotplot in ggplot2'
date: 2023-05-09
permalink: /posts/2023/05/example_dotplot/
tags:
  - dotplot
  - data visualization
  - ggplot2
---

How to generate a quick dotplot of your data in R with ggplot2
======

Here's a template I use to generate something better than barcharts to visualize differences in response between groups.

First, let's simulate some data to visualize. 

```
set.seed(42) # set seed for reproducability
df <- data.frame(
  group = rep(LETTERS[1:3], each = 6),
  value = rnorm(18, mean = 4)
)
```

Notice the data is in tidy format, if your research was recorded like most lab experiments, it might be in wide format. Thankfully, the dplyr package has the `pivot_longer` function which makes converting your data from wide to long format a breeze.

Here is the code I use to create a quick dotplot:
```
library(ggplot2)

my_plot <- ggplot(df, aes(x = group, y = value)) + # these are column names of my dataset
  geom_dotplot(
    binaxis = "y", # this is probably what you want
    stackdir = "center", # for symmetry
    dotsize = 0.8, # adjust along with bindwidth to get desired size
    fill = "white", # this makes the dots circles instead
    binwidth = 0.1 # specifies bin width. Defaults to 1/30 of the range of the data
  ) +
  stat_summary(
    fun.y = mean, # gives horizontal line to compare, can easily change to median
    geom = "errorbar", # make the line appear
    aes(
      ymax = after_stat(y), # upper bound of line
      ymin = after_stat(y), # lower bound of line
      x = group # one line per group
    ),
    width = 0.5, # how wide the line should be
    linetype = 1 # solid or 2 for dashed.
  ) +
  scale_x_discrete(labels = c("Control", "Alfalfa", "Wheat")) + # if x-axis groups need renamed
  labs(title = "Example Dotplot Template", # give your desired title
       x = "Treatment", # label the x axis
       y = "Value") + # label the y axis
  theme_classic() # a ggplot theme
  
my_plot
```
![template dotplot](https://github.com/clstacy/clstacy.github.io/blob/master/images/example_dotplot.png?raw=true)

And there we have it! This can be modified to get what you need, but I hope it is helpful for scientists wanting to visualize their data.

That's a great baseline for getting a feel for how the data looks, but you'll likely want to test for significance for any differences that you might see. 

Testing for significance
------

Fortunately, we can within the ggplot ecosystem test for differences. The code I use to do so is below. I start with the my_plot we made in the code above.

```
library(ggpubr)

my_plot +
  ggpubr::stat_compare_means(comparisons =
                               list(c("A", "B"),
                                    c("B", "C"),
                                    c("A", "C")),
                             method = "t.test",
                             label = "p.signif") + # "p.format" if you want the actual p-value.
                             ggpubr::stat_compare_means(label.y = min(df$value), method = "anova") # add ANOVA p-value.
```
![template dotplot](https://github.com/clstacy/clstacy.github.io/blob/master/images/example_dotplot_comparisons.png?raw=true)

And there we have it!
