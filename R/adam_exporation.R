# load the data
plays <- read.csv("data/plays.csv")

# def_cov <- subset(plays, select = c("pff_passCoverage", "gameId", "playId"))
# player_play_cov <- merge(player_play, def_cov, by = c("gameId", "playId"))

tapply(plays$time)
