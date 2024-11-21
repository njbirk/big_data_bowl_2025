library(tidyverse)
data_dir <- "../data"

play_df <- read_csv(file.path(data_dir, 'plays.csv'))
names(play_df)

player_plays_df <- read.csv(file.path(data_dir, 'player_play.csv'))

unique(play_df$pff_passCoverage)

play_df <- play_df %>%
  select(
    gameId,
    playId,
    passResult,
    passLength,
    passLocationType,
    timeToThrow,
    yardsGained,
    expectedPointsAdded,
    pff_passCoverage,
    pff_manZone,
    possessionTeam,
    defensiveTeam
  ) %>%
  drop_na() %>%
  mutate(
    passResult = factor(passResult),
    passLocationType = factor(passLocationType),
    pff_passCoverage = factor(pff_passCoverage),
    pff_manZone = factor(pff_manZone)
  )

summary(play_df)

tracking_df <- read_csv(file.path(data_dir, 'tracking_week_1.csv'))

gid <- 2022090800
pid <- 56

tracking_df <- tracking_df %>% filter(gameId==gid & playId==pid)

motion <- motion %>% filter(motionSinceLineset==TRUE)
####################################################################################
tracking_df <- left_join(
  tracking_df, 
  select(player_plays_df, gameId, playId, nflId, motionSinceLineset), 
  by = c('gameId', 'playId', 'nflId')
  ) %>% select(-displayName, -jerseyNumber, -event) %>% drop_na()

summary(tracking_df)

tracking_df <- tracking_df %>%
  mutate(
    club = factor(club),
    playDirection = factor(playDirection)
  )

play_df <- play_df %>%
  mutate(
    possessionTeam = factor(possessionTeam),
    defensiveTeam = factor(defensiveTeam)
  )

####################################################################################