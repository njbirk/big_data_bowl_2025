library(tidyverse)
library(caret)

data_dir <- "../data"

game_df <- read_csv(file.path(data_dir, "games.csv"))
play_df <- read_csv(file.path(data_dir, "plays.csv"))
player_plays <- read_csv(file.path(data_dir, "player_play.csv"))
players <- read_csv(file.path(data_dir, "players.csv"))
tracking_df <- read_csv(file.path(data_dir, "cleaned_tracking.csv"))

head(tracking_df)

unique(tracking_df$event)

# Only tracking WRs
receivers <- players %>% filter(position == 'WR')

# Only week 1 games
gameIds <- unique(tracking_df$gameId)

# Only plays with WRs
motion_plays <- player_plays %>%
  filter(motionSinceLineset == TRUE & gameId %in% gameIds & nflId %in% receivers$nflId)

head(motion_plays)

# Only plays with man coverage
man_plays <- play_df %>%
  filter(pff_manZone == "Man")

motion_plays <- motion_plays %>%
  filter(gameId %in% man_plays$gameId & playId %in% man_plays$playId)

head(motion_plays)

gid <- motion_plays$gameId[1]
pid <- motion_plays$playId[1]

play <- tracking_df %>%
  filter(gameId == gid & playId == pid)

# Only look at frames after snap
snap_frame <- play %>%
  filter(frameType == "SNAP") %>%
  pull(frameId) %>%
  first()

play <- play %>% 
  filter(frameId > snap_frame)

# Get the targeted receiver and all relevant defenders
targeted_receiver <- motion_plays%>% 
  filter(gameId == gid & playId == pid) %>% 
  pull(nflId)

defender_positions <- c("linebacker", "cornerback", "safety")

relevant_defenders <- play %>%
  filter(gameId == gid & playId == pid & position_group %in% defender_positions)

head(relevant_defenders)

# We will determine the frame when the pass occurs and the 10 frames leading up to it
unique(play$event)
pass_frame <- play %>% filter(event == "pass_forward") %>% pull(frameId) %>% first()

relevant_frames <- (pass_frame-10):pass_frame

# We will start with the first frame
frame <- relevant_frames[1]

play_frame <- play %>% filter(frameId == frame)

# position function
predict_position <- function(p0, v, a, dir, t) {
  # p0: Initial position (vector of x and y coordinates)
  # v: Initial velocity (scalar, magnitude of velocity)
  # a: Acceleration (scalar, magnitude of acceleration)
  # dir: Direction of motion (angle in degrees, 0 - 360 degrees)
  # t: Time vector (time in seconds at which to calculate position)
  
  # Convert direction from degrees to radians
  dir_rad <- dir * pi / 180
  
  # Decompose velocity and acceleration into components (x and y)
  v_x <- v * cos(dir_rad)
  v_y <- v * sin(dir_rad)
  
  a_x <- a * cos(dir_rad)
  a_y <- a * sin(dir_rad)
  
  # Calculate position for each time point t
  p_t <- p0 + c(v_x, v_y) * t + 0.5 * c(a_x, a_y) * t^2
  
  return(p_t)
}

# First, we need to determine when and where the ball arrives
interception_frame <- play %>% filter(event == "pass_arrived") %>%
  pull(frameId) %>% first()

interception_x <- play %>% 
  filter(frameId == interception_frame & nflId == targeted_receiver) %>%
  pull(x) %>% first()
interception_y <- play %>% 
  filter(frameId == interception_frame & nflId == targeted_receiver) %>%
  pull(y) %>% first()

interception_coords <- c(interception_x, interception_y)

# Now, we can determine the distance between each defender and the interception point
# Since t = 0 is our start frame, we find the time of intercept by subtracting our current frame and dividing by 10 (10 FPS)
t_intercept <- (interception_frame - frame) / 10

# We will calculate the position of each defender at the time of interception
relevant_defenders_frame <- play %>% filter(frameId == frame) %>% filter(position_group %in% defender_positions)

defender_positions <- list()

for (i in 1:nrow(relevant_defenders_frame)) {
  defender <- relevant_defenders_frame[i,]
  
  # Get initial position
  p0 <- c(defender$x, defender$y)
  
  # Get velocity and acceleration
  v <- defender$s
  a <- defender$a
  
  # Get direction of motion
  dir <- defender$dir
  
  # Calculate position at time of interception
  p_t <- predict_position(p0, v, a, dir, t_intercept)
  
  defender_positions <- append(defender_positions, list(p_t))
}

# Now, we can calculate the distances from each defender to the receiver at the time of interception using intercept_coords
distances <- list()
for (i in 1:length(defender_positions)) {
  defender_pos <- defender_positions[[i]]
  
  dist <- sqrt(sum((defender_pos - interception_coords)^2))
  
  distances <- append(distances, list(dist))
}

# Function to calculate the unit vector from defender to receiver
calculate_unit_vector <- function(p_r, p_d) {
  # Calculate the difference in positions (receiver - defender)
  diff <- p_r - p_d
  
  # Calculate the Euclidean distance between the receiver and the defender
  distance <- sqrt(sum(diff^2))
  
  # Calculate the unit vector in the direction from defender to receiver
  unit_vector <- diff / distance
  
  return(unit_vector)
}

# Function to calculate the velocity component in the direction of the receiver
velocity_toward_receiver <- function(v_d, p_r, p_d) {
  # Calculate the unit vector pointing from the defender to the receiver
  unit_vector <- calculate_unit_vector(p_r, p_d)
  
  # Calculate the dot product of the defender's velocity and the unit vector
  v_toward <- sum(v_d * unit_vector)
  
  return(v_toward)
}

# Now, we can calculate relative motion toward interception point for each defender
relative_motions <- list()
for (i in 1:nrow(relevant_defenders_frame)) {
  defender <- relevant_defenders_frame[i,]
  
  # Get defender position
  p_d <- c(defender$x, defender$y)
  
  # Get defender velocity
  # Convert direction from degrees to radians
  dir_rad <- defender$dir * pi / 180
  
  # Decompose velocity and acceleration into components (x and y)
  v_x <- defender$s * cos(dir_rad)
  v_y <- defender$s * sin(dir_rad)
  
  v_d <- c(v_x, v_y)
  
  # Calculate velocity component toward interception point
  v_toward <- velocity_toward_receiver(v_d, interception_coords, p_d)
  
  relative_motions <- append(relative_motions, list(v_toward))
}

# Now, we can weight the relative motions by the inverse of the distance to the receiver (squaring to reduce effect of farther defenders)
weighted_motions <- list()
for (i in 1:length(distances)) {
  dist <- distances[[i]]
  v_toward <- relative_motions[[i]]
  
  weighted_motion <- v_toward / (dist^2)
  
  weighted_motions <- append(weighted_motions, list(weighted_motion))
}

# Now, we can calculate the separation metric as the sum of the weighted relative motions
separation_metric <- sum(unlist(weighted_motions)) * 100

print(separation_metric)

# Now, we can write some functions to do this automatically
get_distances <- function(defenders, interception_coords, t_intercept) {
  distances <- list()
  for (i in 1:nrow(defenders)) {
    defender <- defenders[i,]
    
    # Get initial position
    p0 <- c(defender$x, defender$y)
    
    # Get velocity and acceleration
    v <- defender$s
    a <- defender$a
    
    # Get direction of motion
    dir <- defender$dir
    
    # Calculate position at time of interception
    p_t <- predict_position(p0, v, a, dir, t_intercept)
    
    dist <- sqrt(sum((p_t - interception_coords)^2))
    
    distances <- append(distances, list(dist))
  }
  
  return(distances)
}

get_relative_motions <- function(defenders, interception_coords) {
  relative_motions <- list()
  for (i in 1:nrow(defenders)) {
    defender <- defenders[i,]
    
    # Get defender position
    p_d <- c(defender$x, defender$y)
    
    # Get defender velocity
    # Convert direction from degrees to radians
    dir_rad <- defender$dir * pi / 180
    
    # Decompose velocity and acceleration into components (x and y)
    v_x <- defender$s * cos(dir_rad)
    v_y <- defender$s * sin(dir_rad)
    
    v_d <- c(v_x, v_y)
    
    # Calculate velocity component toward interception point
    v_toward <- velocity_toward_receiver(v_d, interception_coords, p_d)
    
    relative_motions <- append(relative_motions, list(v_toward))
  }
  
  return(relative_motions)
}

calculate_separation_metric <- function(relevant_defenders, interception_coords, t_intercept) {
  # Calculate distances and relative motions
  distances <- get_distances(relevant_defenders, interception_coords, t_intercept)
  relative_motions <- get_relative_motions(relevant_defenders, interception_coords)
  
  # Weight the relative motions by the inverse of the distance to the receiver
  weighted_motions <- list()
  for (i in 1:length(distances)) {
    dist <- distances[[i]]
    v_toward <- relative_motions[[i]]
    
    weighted_motion <- v_toward / (dist^2)
    
    weighted_motions <- append(weighted_motions, list(weighted_motion))
  }
  
  # Calculate the separation metric as the sum of the weighted relative motions
  separation_metric <- sum(unlist(weighted_motions)) * 100
  return(separation_metric)
}

calculate_separation_metric(relevant_defenders_frame, interception_coords, t_intercept)

calculate_separation <- function(gameId, playId) {
  defender_positions <- c("linebacker", "cornerback", "safety")
  
  targeted_receiver <- motion_plays%>% 
    filter(gameId == gid & playId == pid) %>% 
    pull(nflId)
  
  play <- tracking_df %>%
    filter(gameId == gid & playId == pid)
  
  # Get interception coords
  interception_frame <- play %>% filter(event == "pass_arrived") %>%
    pull(frameId) %>% first()
  
  interception_x <- play %>% 
    filter(frameId == interception_frame & nflId == targeted_receiver) %>%
    pull(x) %>% first()
  interception_y <- play %>% 
    filter(frameId == interception_frame & nflId == targeted_receiver) %>%
    pull(y) %>% first()
  
  interception_coords <- c(interception_x, interception_y)
  
  pass_frame <- play %>% filter(event == "pass_forward") %>% pull(frameId) %>% first()
  relevant_frames <- (pass_frame-10):pass_frame
  
  separation_metrics <- list()
  
  for (frame in relevant_frames) {
    t_intercept <- (interception_frame - frame) / 10
    play_frame <- play %>% filter(frameId == frame)
    
    relative_defenders <- play_frame %>% 
      filter(position_group %in% defender_positions)
    
    separation_metric <- calculate_separation_metric(relative_defenders, interception_coords, t_intercept)
    
    separation_metrics <- append(separation_metrics, list(separation_metric))
  }
  return(separation_metrics)
}

test <- unlist(calculate_separation(gid, pid))
test
