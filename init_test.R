# load all play data
play_data <- read.csv("data/plays.csv")
play_data

# load player data
player_play_data <- read.csv("data/player_play.csv")
player_play_data

# merge
total_play_data <- merge(play_data, player_play_data, by = "playId")

# test plot
