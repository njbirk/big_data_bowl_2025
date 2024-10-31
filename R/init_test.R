# load all play data
play_data <- read.csv("../data/plays.csv")
play_data

# load player data
player_play_data <- read.csv("../data/player_play.csv")
player_play_data

# merge
total_play_data <- merge(play_data, player_play_data, by = "playId")

summary(total_play_data)


library(dplyr)
library(tidyr)

total_play_data <- distinct(total_play_data)
summary(total_play_data)

get_mode <- function(x) {
  unique_x <- unique(x)
  unique_x[which.max(tabulate(match(x, unique_x)))]
}

# 
offense <- total_play_data %>%
  group_by(possessionTeam, offenseFormation) %>%
  summarize(
    numPlays = n(),
    avgYrds = mean(yardsGained, na.rm = TRUE),
    mostCommonDown = get_mode(down),
    avgGain = mean(yardsGained[yardsGained > 0], na.rm = TRUE),
    avgLoss = mean(yardsGained[yardsGained <= 0], na.rm = TRUE),
    .groups = "drop"
  ) %>%
  drop_na() %>%
  group_by(possessionTeam) %>%
  mutate(avgTotalYrds = mean(avgYrds, na.rm = TRUE)) %>%
  ungroup() %>%
  mutate(yardDiff = avgYrds - avgTotalYrds)
  

offense

lions <- offense %>% 
  filter(possessionTeam == "DET") %>% 
  arrange(desc(yardDiff))

lions %>% arrange(avgLoss)

