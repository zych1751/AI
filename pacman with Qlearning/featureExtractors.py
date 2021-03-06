# featureExtractors.py
# --------------------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


"Feature extractors for Pacman game states"

from game import Directions, Actions
import util

class FeatureExtractor:
    def getFeatures(self, state, action):
        """
          Returns a dict from features to counts
          Usually, the count will just be 1.0 for
          indicator functions.
        """
        util.raiseNotDefined()

class IdentityExtractor(FeatureExtractor):
    def getFeatures(self, state, action):
        feats = util.Counter()
        feats[(state,action)] = 1.0
        return feats

class CoordinateExtractor(FeatureExtractor):
    def getFeatures(self, state, action):
        feats = util.Counter()
        feats[state] = 1.0
        feats['x=%d' % state[0]] = 1.0
        feats['y=%d' % state[0]] = 1.0
        feats['action=%s' % action] = 1.0
        return feats

def closestFood(pos, food, walls):
    """
    closestFood -- this is similar to the function that we have
    worked on in the search project; here its all in one place
    """

    fringe = [(pos[0], pos[1], 0)]
    expanded = set()
    while fringe:
        pos_x, pos_y, dist = fringe.pop(0)
        if (pos_x, pos_y) in expanded:
            continue
        expanded.add((pos_x, pos_y))
        # if we find a food at this location then exit
        if food[pos_x][pos_y]:
            return dist
        # otherwise spread out from the location to its neighbours
        nbrs = Actions.getLegalNeighbors((pos_x, pos_y), walls)
        for nbr_x, nbr_y in nbrs:
            fringe.append((nbr_x, nbr_y, dist+1))
    # no food found
    return None


class SimpleExtractor(FeatureExtractor):
    """
    Returns simple features for a basic reflex Pacman:
    - whether food will be eaten
    - how far away the next food is
    - whether a ghost collision is imminent
    - whether a ghost is one step away
    """

    def getFeatures(self, state, action):
        # extract the grid of food and wall locations and get the ghost locations
        food = state.getFood()
        walls = state.getWalls()
        ghosts = state.getGhostPositions()
        ghostsStates = state.getGhostStates()

        features = util.Counter()

        features["bias"] = 1.0

        # compute the location of pacman after he takes the action
        x, y = state.getPacmanPosition()
        dx, dy = Actions.directionToVector(action)
        next_x, next_y = int(x + dx), int(y + dy)

        # count the number of ghosts 1-step away
        features["#-of-ghosts-1-step-away"] = sum((next_x, next_y) in Actions.getLegalNeighbors(g, walls) for g in ghosts)

        # if there is no danger of ghosts then add the food feature
        if not features["#-of-ghosts-1-step-away"] and food[next_x][next_y]:
            features["eats-food"] = 1.0

        dist = closestFood((next_x, next_y), food, walls)
        if dist is not None:
            # make the distance a number less than one otherwise the update
            # will diverge wildly
            features["closest-food"] = float(dist) / (walls.width * walls.height)
        features.divideAll(10.0)
        return features

class CustomExtractor(FeatureExtractor):
    """
    Generate your own feature
    """

    distance_map = {}
    map_check = False

    def fillMap(self, walls):
        for temp_x in range(0, walls.width):
            for temp_y in range(0, walls.height):
                fringe = [(temp_x, temp_y, 0)]
                
                while fringe:
                    pos_x, pos_y, dist = fringe.pop(0)
                    if ((temp_x, temp_y), (float(pos_x), float(pos_y))) in self.distance_map:
                        continue
                    self.distance_map[((temp_x, temp_y), (float(pos_x), float(pos_y)))] = dist

                    nbrs = Actions.getLegalNeighbors((pos_x, pos_y), walls)
                    for nbr_x, nbr_y in nbrs:
                        fringe.append((nbr_x, nbr_y, dist+1))
                        self.distance_map[((temp_x, temp_y), ((float(pos_x)+nbr_x)/2, (float(pos_y)+nbr_y)/2))] = dist+0.5

    def dis(self, pos1, pos2):
        pos2 = (float(pos2[0]), float(pos2[1]))
        return self.distance_map[(pos1, pos2)]
        #return abs(pos1[0]-pos2[0]) + abs(pos1[1] - pos2[1])

    def getFeatures(self, state, action):
        "*** YOUR CODE HERE ***"
        food = state.getFood()
        walls = state.getWalls()
        ghosts = state.getGhostPositions()
        ghostsStates = state.getGhostStates()

        if not self.map_check:
            self.map_check = True;
            self.fillMap(walls)

        features = util.Counter()

        features["bias"] = 1.0

        # compute the location of pacman after he takes the action
        x, y = state.getPacmanPosition()
        dx, dy = Actions.directionToVector(action)
        next_x, next_y = int(x + dx), int(y + dy)

        # count the number of ghosts 1-step away
        features["#-of-ghosts-1-step-away"] = sum((next_x, next_y) in Actions.getLegalNeighbors(g, walls) for g in ghosts)
        
        dist = closestFood((next_x, next_y), food, walls)
        ghost1_dist = self.dis((next_x, next_y), ghosts[0])
        prev1_dist = self.dis((x, y), ghosts[0])
        ghost2_dist = self.dis((next_x, next_y), ghosts[1])
        prev2_dist = self.dis((x, y), ghosts[1])
        ghostScaredTime1 = state.data.agentStates[1].scaredTimer
        ghostScaredTime2 = state.data.agentStates[2].scaredTimer

        checked = False
        if ghostScaredTime1 > ghost1_dist/2 or ghostScaredTime1 > 20:
            if prev1_dist > ghost1_dist:
                if ghost1_dist > 0 and ghost1_dist < 987654321:
                    checked = True
                    features["eats-ghost"] += 1 / float(ghost1_dist) 
                elif ghost1_dist < 0.5:
                    checked = True
                    features["eats-ghost"] += 1.0
        if ghostScaredTime2 > ghost2_dist/2 or ghostScaredTime2 > 20:
            if prev2_dist > ghost2_dist:
                if ghost2_dist > 0 and ghost2_dist < 987654321:
                    checked = True
                    features["eats-ghost"] += 1 / float(ghost2_dist)
                elif ghost2_dist < 0.5:
                    checked = True
                    features["eats-ghost"] += 1.0
        if (ghostScaredTime1 < 3 and prev1_dist < 3 and prev1_dist > ghost1_dist) or (ghostScaredTime2 < 3 and prev2_dist < 3 and prev2_dist > ghost2_dist):
            features["escape-ghost"] = -1.0
            checked = True
            
        if not checked:
            if dist is not None and ghostScaredTime1 < 10 and ghostScaredTime2 < 10:
                # make the distance a number less than one otherwise the update
                # will diverge wildly
                features["closest-food"] = float(dist) / (walls.width * walls.height) * 2
            elif not features["#-of-ghosts-1-step-away"] and food[next_x][next_y]:
                features["eats-food"] = 1.0

        features.divideAll(3.0)

        return features
