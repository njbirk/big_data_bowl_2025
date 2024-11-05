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

# Add back to tracking data and add distance column
agg_tracking_df$losX <- at_snap$losX
agg_tracking_df$losDist <- abs(agg_tracking_df$atSnapX - agg_tracking_df$losX)
summary(agg_tracking_df)

# Convert home and visitor scores and probabilities to possession and defensive team scores and probablities
plays_df <- plays_df %>%
  left_join(select(game_df, gameId, homeTeamAbbr, visitorTeamAbbr), by = "gameId") %>%
  mutate(
    possessionTeamScore = if_else(homeTeamAbbr == possessionTeam, preSnapHomeScore, preSnapVisitorScore),
    defensiveTeamScore = if_else(homeTeamAbbr == defensiveTeam, preSnapHomeScore, preSnapVisitorScore),
    preSnapPossessionTeamWinProbability = if_else(homeTeamAbbr == possessionTeam, preSnapHomeTeamWinProbability, preSnapVisitorTeamWinProbability),
    preSnapDefensiveTeamWinProbability = if_else(homeTeamAbbr == defensiveTeam, preSnapHomeTeamWinProbability, preSnapVisitorTeamWinProbability)
  )

# Only keep essential columns
names(plays_df)
plays_df <- plays_df %>%
  select(
    gameId,
    playId,
    quarter,
    down,
    possessionTeamScore,
    defensiveTeamScore,
    preSnapPossessionTeamWinProbability,
    preSnapDefensiveTeamWinProbability,
    absoluteYardlineNumber,
    yardsToGo,
    numLinemen,
    numLBs,
    numDBs,
    numSafeties,
    playClockAtSnap,
    blitz
  )

# Join into tracking data
training_df <- left_join(agg_tracking_df, plays_df, by = c("gameId", "playId"))
names(training_df)

# Divide into training and test sets
library(caret)
train_index <- createDataPartition(training_df$blitz, p = 0.7, list = FALSE)
train_set <- training_df[train_index, ]
test_set <- training_df[-train_index, ]

# separate into features and labels
trainX <- train_set %>% ungroup() %>% select(-gameId, -playId, -nflId, -atSnapDirection, -blitz)
trainY <- train_set$blitz

testX <- test_set %>% ungroup() %>% select(-gameId, -playId, -nflId, -atSnapDirection, -blitz)
testY <- test_set$blitz

# prepping for training
dtrain <- xgb.DMatrix(data = as.matrix(trainX), label = trainY)
dtest <- xgb.DMatrix(data = as.matrix(testX), label = testY)

params <- list(
  objective = "binary:logistic",  # Binary classification
  eval_metric = "auc",         # Evaluation metric
  max_depth = 3,                   # Maximum depth of trees
  eta = 0.1                        # Learning rate
)

# Training
xgb_model <- xgb.train(
  params = params, 
  data = dtrain, 
  nrounds = 100
)

# Prediction
predictions <- predict(xgb_model, dtest)

# Convert predictions to binary (0/1)
predictedY <- ifelse(predictions > 0.5, 1, 0)

# Evaluate the model performance
testY <- factor(testY)
predictedY <- factor(predictedY)

# Ensure both factors have the same levels
levels(predictedY) <- levels(testY)

# Create the confusion matrix
confusionMatrix(predictedY, testY)
