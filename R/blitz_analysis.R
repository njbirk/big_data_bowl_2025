library(dplyr)
library(ggplot2)
library(xgboost)

game_df <- read.csv("../data/games.csv")
plays_df <- read.csv("../data/blitz_plays.csv")
player_plays_df <- read.csv("../data/player_play.csv")
players_df <- read.csv("../data/players.csv")
tracking_df <- read.csv("../data/tracking_week_1.csv")

# List of defensive positions
def_positions <- c('DT', 'LB', 'ILB', 'MLB', 'OLB', 'CB', 'SS', 'FS', 'DE', 'NT', 'DB')

# Only keep essential positions
def_plus_qb <- c(def_positions, 'QB')
players_df <- players_df %>% filter(position %in% def_plus_qb)

tracking_df <- tracking_df %>% filter(nflId %in% players_df$nflId)
player_plays_df <- player_plays_df %>% filter(nflId %in% players_df$nflId)

# Only keep games & plays in week 1
games <- unique(tracking_df$gameId)

game_df <- game_df %>% filter(gameId %in% games)
plays_df <- plays_df %>% filter(gameId %in% games)
player_plays_df <- player_plays_df %>% filter(gameId %in% games)

# Grouping defensive positions by type
dline_pos <- c('DT', 'DE', 'NT')
lb_pos <- c('LB', 'ILB', 'MLB', 'OLB')
db_pos <- c('CB', 'DB')
safety_pos <- c('SS', 'FS')

# Joining player play data with position/name data
players_df <- inner_join(player_plays_df, players_df, by = "nflId")

# Adding count of defenders by position
position_df <- players_df %>%
  group_by(gameId, playId) %>%
  summarise(
    numLinemen = sum(position %in% dline_pos),
    numLBs = sum(position %in% lb_pos),
    numDBs = sum(position %in% db_pos),
    numSafeties = sum(position %in% safety_pos),
    totalDefenders = sum(!position %in% c('QB')),
    .groups = "keep"
  )

plays_df <- inner_join(plays_df, position_df, by = c('gameId', 'playId'))

# Get aggregate stats for every player using tracking data
tracking_df <- tracking_df %>% filter(frameType %in% c("BEFORE_SNAP", "SNAP"))

agg_tracking_df <- tracking_df %>%
  group_by(gameId, playId, nflId) %>%
  mutate(
    # Initial XY position
    initialX = if_else(frameId == 1, x, NA_real_),
    initialY = if_else(frameId == 1, y, NA_real_),
    
    # At snap speed and XY position
    atSnapSpeed = if_else(frameType == "SNAP", s, NA_real_),
    atSnapX = if_else(frameType == "SNAP", x, NA_real_),
    atSnapY = if_else(frameType == "SNAP", y, NA_real_),
    
    # Direction at snap
    atSnapDirection = if_else(frameType == "SNAP", playDirection, NA_character_)
  ) %>%
  summarise(
    initialX = first(na.omit(initialX)),
    initialY = first(na.omit(initialY)),
    atSnapSpeed = first(na.omit(atSnapSpeed)),
    atSnapX = first(na.omit(atSnapX)),
    atSnapY = first(na.omit(atSnapY)),
    atSnapDirection = first(na.omit(atSnapDirection)),
    avgSpeed = mean(s, na.rm = TRUE),
    preSnapDist = sum(dis, na.rm = TRUE),
    .groups = "keep"
  )

# Next, need to calculate distance from LOS for every player
# First, need to find absolute X value of LOS
# Get snap X position and direction and LOS for all plays
at_snap <- agg_tracking_df %>% select(atSnapX)
los <- plays_df %>% select(gameId, playId, yardlineNumber)

# Next need to convert yardLineNumber to scale used in tracking_df
# Function to get true LOS in XY scale
get_los_x <- function(x, los) {
  if (x > 60) {
    return(100 - los + 10)
  }
  else {
    return(los + 10)
  }
}

at_snap <- left_join(at_snap, los, by = c('gameId', 'playId'))
at_snap <- at_snap %>%
  mutate(losX = get_los_x(atSnapX, yardlineNumber))

# Add back to tracking data
agg_tracking_df$losX <- at_snap$losX
summary(agg_tracking_df)

# Next, need to calculate the box for every play and add a bool for whether or not players are in it

