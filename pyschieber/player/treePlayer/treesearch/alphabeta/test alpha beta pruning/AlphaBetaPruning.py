"""Testing a low level alpha beta pruning algorithm.

Returns:
    _type_: _description_
"""

import random
from time import time

class Node:

    def __init__(self, value = None):
        self.children = None # List of nodes
        self.value = value
    
    def populate(self, depth, width):
        if depth > 1:
            self.children = []
            for _ in range(width):
                self.children.append(Node()) # Do NEVER use vectorized version to create nodes. They will all be the same! bsp.: [Node()] * 5
            for child in self.children:
                child.populate(depth = depth-1, width = width)
        else:
            self.children = []
            for _ in range(width):
                self.children.append(Node(random.randint(1,100)))
    
def plot(node, indent = ""):
    print(indent + str(node.value))
    indent += "-"
    if node.children is not None:
        for child in node.children:
            plot(child, indent)
        

class AlphaBeta:
    """alpha beta search very basic.

    Returns:
        _type_: _description_
    """

    def __init__(self, game_tree):
        self.game_tree = game_tree
        return

    def alpha_beta_search(self, node = None): # this can be implemented better.
        if node is None:
            node = self.game_tree
        infinity = float('inf')
        best_val = -infinity
        beta = infinity

        successors = self.getSuccessors(node)
        best_state = None
        for state in successors:
            value = self.min_value(state, best_val, beta)
            # node.value = value # Fill in None with value. (optional)
            if value > best_val:
                best_val = value
                best_state = state
        # print "AlphaBeta:  Utility Value of Root Node: = " + str(best_val)
        # print "AlphaBeta:  Best State is: " + best_state.Name
        return best_state, best_val

    def max_value(self, node, alpha, beta):
        # print "AlphaBeta–>MAX: Visited Node :: " + node.Name
        if self.isTerminal(node):
            return self.getUtility(node)
        infinity = float('inf')
        value = -infinity

        successors = self.getSuccessors(node)
        for state in successors:
            value = max(value, self.min_value(state, alpha, beta))
            # node.value = value # Fill in None with value. (optional)
            if value >= beta:
                return value
            alpha = max(alpha, value)
        return value

    def min_value(self, node, alpha, beta):
        # print "AlphaBeta–>MIN: Visited Node :: " + node.Name
        if self.isTerminal(node):
            return self.getUtility(node)
        infinity = float('inf')
        value = infinity

        successors = self.getSuccessors(node)
        for state in successors:
            value = min(value, self.max_value(state, alpha, beta))
            # node.value = value # Fill in None with value. (optional)
            if value <= alpha:
                return value
            beta = min(beta, value)

        return value
    #                     #
    #   UTILITY METHODS   #
    #                     #

    def getSuccessors(self, node):
        """successor states in a game tree are the child nodes…

        Args:
            node (Node): Class

        Returns:
            list: list of Nodes
        """
        assert node is not None
        return node.children

    def isTerminal(self, node):
        """     # return true if the node has NO children (successor states)
                # return false if the node has children (successor states)

        Args:
            node (Node): Node instance of the Node Class

        Returns:
            bool: Node has children (T)
        """
        assert node is not None
        return node.children is None

    def getUtility(self, node):
        assert node is not None
        return node.value

if __name__ == "__main__":
    """Creates a tree and then uses the AlphaBeta class to traverse it.

    Returns:
        None: None
    """

    depth = 9
    width = 4

    start = time()
    tree = Node()
    tree.populate(depth, width)
    # plot(tree)
    AlphaBetaTree = AlphaBeta(tree)
    startPrune = time()
    best_state, best_val = AlphaBetaTree.alpha_beta_search()
    end = time()
    print("alpha beta value: ", best_val)
    # plot(tree)
    print('time spent pruning: ', end-startPrune)
    print('time spent for everything: ', end-start)