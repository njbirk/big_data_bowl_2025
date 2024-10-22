# load all play data
play_data <- read.csv("data/plays.csv")
play_data

# load player data
player_play_data <- read.csv("data/player_play.csv")
player_play_data

# merge
total_play_data <- merge(play_data, player_play_data, by = "playId")

# testing with db
install.packages("RSQLite")
library(DBI)
conn <- dbConnect(RSQLite::SQLite(), "play_data.db")

dbWriteTable(conn, "play_data", play_data)
dbWriteTable(conn, "player_play_data", play_data)

# test query
result <- dbGetQuery(conn, "SELECT DISTINCT possessionTeam FROM play_data")
result

dbDisconnect(conn)
