library(tidyverse)

source("utils.R")
data_dir <- "../data"

suppressMessages({
  plays <- read_csv(file.path(data_dir, "plays.csv"))
  players <- read_csv(file.path(data_dir, "players.csv"))
  player_plays <- read_csv(file.path(data_dir, "player_play.csv"))
  tracking <- read_csv(file.path(data_dir, "tracking_week_1.csv"))
})

# Only tracking WRs
receivers <- players %>% filter(position == 'WR')

# Only week 1 games
gameIds <- unique(tracking$gameId)

# Only plays with WRs
motion_plays <- player_plays %>%
  filter(motionSinceLineset == TRUE & gameId %in% gameIds & nflId %in% receivers$nflId)

# Get motion startpoints for all plays
motion_starts <- list()
for (i in 1:nrow(motion_plays)) {
  play <- motion_plays[i,]
  
  play_data <- tracking %>%
    filter(gameId == play$gameId & playId == play$playId & nflId == play$nflId)
  
  motion_start <- get_motion_start(play_data)
  motion_starts <- append(motion_starts, list(motion_start))
}
