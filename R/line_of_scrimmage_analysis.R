library(dplyr)
library(ggplot2)

plays_df <- read.csv("../data/blitz_plays.csv")
tracking_df <- read.csv("../data/defensive_tracking.csv")

gid <- 2022090800
pid <- 692

tracking_df <- tracking_df %>% filter(gameId == gid)
plays_df <- plays_df %>% filter(gameId == gid)
summary(tracking_df)

presnap_df <- tracking_df %>% filter(frameType %in% c("BEFORE_SNAP", "SNAP"))
head(presnap_df)

get_los_dist <- function(playid, nflid) {
  play <- plays_df %>% filter(playId == playid)
  if (nrow(play) == 0) {
    return(NA)  # or another appropriate value
  }
  los <- play$yardlineNumber
  
  tracking_play <- tracking_df %>% 
    filter((playId == playid) & (nflId == nflid) & (frameType == "SNAP"))
  
  pos <- ifelse(tracking_play$x > 50, 100 - tracking_play$x, tracking_play$x)
  if (nrow(tracking_play) == 0) {
    return(NA)  # or another appropriate value
  }
  return(abs(pos - los))
}

presnap_player_df <- presnap_df %>%
  group_by(playId, nflId) %>%
  summarise(
    max_dist = sum(dis, na.rm = TRUE),
    top_speed = max(s, na.rm = TRUE),
    avg_speed = mean(s, na.rm = TRUE),
    .groups = "keep"
  ) %>%
  mutate(los_dist = get_los_dist(playId, nflId))


get_los_dist(56, 38577)

presnap_player_df

plays_grouped <- presnap_player_df %>%
  group_by(playId) %>%
  summarise(
    mean_los_dist = mean(los_dist, na.rm = TRUE),
    min_los_dist = min(los_dist, na.rm = TRUE),
    count_los_dist = sum(los_dist < 2)
    ) %>%
  mutate(snap_frame = plays_df)

plays_grouped[plays_grouped$playId == 2688,]

head(plays_df)
