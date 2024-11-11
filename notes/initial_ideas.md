# Big Data Bowl Initial Analysis and Ideas

# Initial Ideas

## Blitz Analysis

- Could identify plays as blitzes and use play data (defensive formation, line motion, etc.) and tracking data to classify plays as blitzes based on presnap information
- Could then identify deep/big plays and determine impact of blitz on offense's ability to throw downfield
    - Gives offenses cues to look for to audible when blitz is expected

## WR Motion

- How effective is motion at determining defensive coverage? 
- Which WRs are best at motioning?
- Which QBs are best at reading coverage?

## Risk/Opportunity Analysis

- Could analyze how suseptible the defense's formation is to short pass, deep pass, rush, pass to particular receiver, etc.
- This could be used by the offense to identify a play that might be success based on where the defense lines up and call an audible.

## Clustering

* Cluster player-frames by position on the field and position relative to ball/other players on same team
    * Goal is to be able to classify players by where they line up

|Relative to ball|relative to player $i$ (for all $i$)|
|-|-|
|$(x,y)-(x_{fb},y_{fb})$|$(x,y)-(x_{P_i},y_{P_i})$|

# Initial Cleaning/Analysis


