library(tidyverse)
library(splines)

get_motion_start <- function(play) {
  # Fit spline curve to speed data
  spline_fit <- smooth.spline(play$frameId, play$s)
  
  # Get the second derivative of the spline curve
  jerk <- predict(spline_fit, x = play$frameId, deriv = 2)$y
  
  # Remove frames at/after snap
  snap <- play %>% filter(frameType == "SNAP") %>%
    pull(frameId) %>%
    first()
  jerk <- jerk[1:snap-1]
  
  # Find the frame with the maximum jerk
  max_jerk <- which.max(jerk)
  
  return(max_jerk)
}

