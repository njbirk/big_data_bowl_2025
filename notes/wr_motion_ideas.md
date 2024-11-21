# Wide Receive Motion Research Questions and Feature Engineering

## Main Research Problem

**What is the impact pre-snap wide receiver motion on post-snap play?**

## Research Questions

- What types of motion are most effective?
    - What makes motion effective?
- What impact does a motion have on a defense?
    - Disruption, change of coverage, mismatches, etc.
- How does motion influence QB play?
    - Are certain QBs better at using motion to make better reads?
    - Are specific types of motion more helpful for QBs?

## Feature Engineering Idea: Graphical Representation

For every play, we can represent the formation of both the offense and the defense as a graph, where the nodes represent individual players and their individual stats and the edges represent the relationships between players. 

Node Information:

- Player ID
- Player Position (on team)
- Player Position (on field)
- Velocity
- Acceleration
- Direction
    
Edge Ideas:

- Distance between players
- Coverage assignments
- Position group

We can use these assignments to measure defense disruption:

- Because coverage assignments are edges, we can adjust these frame by frame
    - We can count the number of coverage changes for man defense
    - For zone, we can count the number of offensive players in a zone (determinined by clustering)
    - More coverage changes -> more disruption
- We can also measure distance covered, and total movement of defenders, especially within the same position group
