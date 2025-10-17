"""
Python bindings for the DSM library
"""
from __future__ import annotations
import collections.abc
import typing
__all__: list[str] = ['AdjacencyMatrix', 'CRITICAL', 'DEBUG', 'DOUBLE_TAIL', 'Dynamics', 'ERROR', 'INFO', 'Itinerary', 'LENGTH', 'LogLevel', 'Measurement', 'OFF', 'PathWeight', 'RoadNetwork', 'SINGLE_TAIL', 'TRACE', 'TRAVELTIME', 'TrafficLightOptimization', 'WARN', 'WEIGHT', 'get_log_level', 'set_log_level']
class AdjacencyMatrix:
    def __call__(self, arg0: typing.SupportsInt, arg1: typing.SupportsInt) -> bool:
        """
        Description
        Get the link at the specified row and column.
        
        Args
          Id row: The row index of the element 
          Id col: The column index of the element 
        
        Returns
          bool: True if the link exists, false otherwise
        """
    @typing.overload
    def __init__(self) -> None:
        """
        Description
        Construct a new
        
        Args
          std::string const & fileName: The name of the file containing the adjacency matrix 
        
        Returns
          void: No return value
        """
    @typing.overload
    def __init__(self, fileName: str) -> None:
        """
        Description
        Construct a new
        
        Args
          std::string const & fileName: The name of the file containing the adjacency matrix 
        
        Returns
          void: No return value
        """
    def clear(self) -> None:
        """
        Description
        Clear the adjacency matrix.
        
        Args
          None
        
        Returns
          void: No description
        """
    def clearCol(self, arg0: typing.SupportsInt) -> None:
        """
        Description
        Clear the column at the specified index. 
        The dimension of the matrix does not change.
        
        Args
          Id col: No description
        
        Returns
          void: No description
        """
    def clearRow(self, arg0: typing.SupportsInt) -> None:
        """
        Description
        Clear the row at the specified index. 
        The dimension of the matrix does not change.
        
        Args
          Id row: No description
        
        Returns
          void: No description
        """
    def contains(self, arg0: typing.SupportsInt, arg1: typing.SupportsInt) -> bool:
        """
        Description
        Check if the link row -> col exists in the adjacency matrix.
        
        Args
          Id row: The row index of the element 
          Id col: The column index of the element 
        
        Returns
          bool: True if the link exists, false otherwise
        """
    def elements(self) -> list[tuple[int, int]]:
        """
        Description
        Get a vector containing all the links in the adjacency matrix as pairs of nodes.
        
        Args
          None
        
        Returns
          std::vector< std::pair< Id, Id > >: A vector containing all the links in the adjacency matrix as pairs of nodes 
        """
    def empty(self) -> bool:
        """
        Description
        Check if the adjacency matrix is empty.
        
        Args
          None
        
        Returns
          bool: True if the adjacency matrix is empty, false otherwise 
        """
    def getCol(self, arg0: typing.SupportsInt) -> list[int]:
        """
        Description
        Get the column at the specified index.
        
        Args
          Id col: The column index 
        
        Returns
          std::vector< Id >: The column at the specified index 
        """
    def getInDegreeVector(self) -> list[int]:
        """
        Description
        Get the input degree vector of the adjacency matrix.
        
        Args
          None
        
        Returns
          std::vector< int >: The input degree vector of the adjacency matrix 
        """
    def getOutDegreeVector(self) -> list[int]:
        """
        Description
        Get the output degree vector of the adjacency matrix.
        
        Args
          None
        
        Returns
          std::vector< int >: The output degree vector of the adjacency matrix 
        """
    def getRow(self, arg0: typing.SupportsInt) -> list[int]:
        """
        Description
        Get the row at the specified index.
        
        Args
          Id row: The row index 
        
        Returns
          std::vector< Id >: The row at the specified index 
        """
    def insert(self, arg0: typing.SupportsInt, arg1: typing.SupportsInt) -> None:
        """
        Description
        Inserts the link row -> col in the adjacency matrix.
        
        Args
          Id row: The row index of the element 
          Id col: The column index of the element
        
        Returns
          void: No description
        """
    def n(self) -> int:
        """
        Description
        Get the number of nodes in the adjacency matrix.
        
        Args
          None
        
        Returns
          size_t: The number of nodes in the adjacency matrix 
        """
    def read(self, fileName: str) -> None:
        """
        Description
        Read the adjacency matrix from a binary file.
        
        Args
          std::string const & fileName: The name of the file containing the adjacency matrix 
        
        Returns
          void: No description
        """
    def save(self, fileName: str) -> None:
        """
        Description
        Write the adjacency matrix to a binary file.
        
        Args
          std::string const & fileName: The name of the file where the adjacency matrix will be written 
        
        Returns
          void: No description
        """
    def size(self) -> int:
        """
        Description
        Get the number of links in the adjacency matrix.
        
        Args
          None
        
        Returns
          size_t: The number of links in the adjacency matrix 
        """
class Dynamics:
    def __init__(self, graph: RoadNetwork, useCache: bool = False, seed: typing.SupportsInt | None = None, alpha: typing.SupportsFloat = 0.0, weightFunction: PathWeight = ..., weightThreshold: typing.SupportsFloat | None = None) -> None:
        """
        Description
        Construct a new First Order
        
        Args
          RoadNetwork graph: The graph representing the network 
          bool useCache: If true, the cache is used (default is false) 
          std::optional< unsigned int > seed: The seed for the random number generator (default is std::nullopt) 
          double alpha: The minimum speed rate (default is 0) 
          PathWeight const weightFunction: The dsf::PathWeight function to use for the pathfinding (default is dsf::PathWeight::TRAVELTIME) 
          std::optional< double > weightTreshold: The weight threshold for the pathfinding (default is std::nullopt) 
        
        Returns
          void: No return value
        """
    @typing.overload
    def addAgentsRandomly(self, nAgents: typing.SupportsInt) -> None:
        """
        Description
        No description available.
        
        Args
          Size nAgents: No description
        
        Returns
          void: No description
        """
    @typing.overload
    def addAgentsRandomly(self, nAgents: typing.SupportsInt, src_weights: collections.abc.Mapping[typing.SupportsInt, typing.SupportsFloat], dst_weights: collections.abc.Mapping[typing.SupportsInt, typing.SupportsFloat]) -> None:
        """
        Description
        No description available.
        
        Args
          Size nAgents: No description
        
        Returns
          void: No description
        """
    def addAgentsUniformly(self, nAgents: typing.SupportsInt, itineraryId: typing.SupportsInt | None = None) -> None:
        """
        Description
        Add agents uniformly on the road network.
        
        Args
          Size nAgents: The number of agents to add 
          std::optional< Id > itineraryId: The id of the itinerary to use (default is std::nullopt) 
        
        Returns
          void: No description
        """
    def evolve(self, reinsert_agents: bool = False) -> None:
        """
        Description
        Evolve the simulation. 
        Evolve the simulation by moving the agents and updating the travel times. In particular:
        
        Args
          bool reinsert_agents: If true, the agents are reinserted in the simulation after they reach their destination 
        
        Returns
          void: No description
        """
    def initTurnCounts(self) -> None:
        """
        Description
        Initialize the turn counts map.
        
        Args
          None
        
        Returns
          void: No description
        """
    def meanSpireInputFlow(self, resetValue: bool = True) -> Measurement:
        """
        Description
        Get the mean spire input flow of the streets in
        
        Args
          bool resetValue: If true, the spire input/output flows are cleared after the computation 
        
        Returns
          Measurement: No description
        """
    def meanSpireOutputFlow(self, resetValue: bool = True) -> Measurement:
        """
        Description
        Get the mean spire output flow of the streets in
        
        Args
          bool resetValue: If true, the spire output/input flows are cleared after the computation 
        
        Returns
          Measurement: No description
        """
    def meanTravelDistance(self, clearData: bool = False) -> Measurement:
        """
        Description
        Get the mean travel distance of the agents in
        
        Args
          bool clearData: If true, the travel distances are cleared after the computation 
        
        Returns
          Measurement: No description
        """
    def meanTravelSpeed(self, clearData: bool = False) -> Measurement:
        """
        Description
        Get the mean travel speed of the agents in
        
        Args
          bool clearData: If true, the travel times and distances are cleared after the computation 
        
        Returns
          Measurement: No description
        """
    def meanTravelTime(self, clearData: bool = False) -> Measurement:
        """
        Description
        Get the mean travel time of the agents in
        
        Args
          bool clearData: If true, the travel times are cleared after the computation 
        
        Returns
          Measurement: No description
        """
    def nAgents(self) -> int:
        """
        Description
        Get the number of agents currently in the simulation.
        
        Args
          None
        
        Returns
          Size: Size The number of agents 
        """
    def normalizedTurnCounts(self) -> dict:
        """
        Description
        Get the normalized turn counts of the agents.
        
        Args
          None
        
        Returns
          std::unordered_map< Id, std::unordered_map< Id, double > > const: const std::unordered_map<Id, std::unordered_map<Id, double>>& The normalized turn counts. The outer map's key is the street id, the inner map's key is the next street id and the value is the normalized number of counts 
        """
    def optimizeTrafficLights(self, optimizationType: TrafficLightOptimization = TrafficLightOptimization.DOUBLE_TAIL, logFile: str = '', threshold: typing.SupportsFloat = 0.0, ratio: typing.SupportsFloat = 1.3) -> None:
        """
        Description
        Optimize the traffic lights by changing the green and red times.
        
        Args
          TrafficLightOptimization optimizationType: TrafficLightOptimization, The type of optimization. Default is DOUBLE_TAIL 
          const std::string & logFile: The file into which write the logs (default is empty, meaning no logging) 
          double const percentage: double, the maximum amount (percentage) of the green time to change (default is 0.3) 
          double const threshold: double, The ratio between the self-density and neighbour density to trigger the non-local optimization (default is 1.3)
        
        Returns
          void: No description
        """
    def saveInputStreetCounts(self, filename: str, reset: bool = False, separator: str = ';') -> None:
        """
        Description
        Save the street input counts in csv format.
        
        Args
          const std::string & filename: The name of the file 
          bool reset: If true, the input counts are cleared after the computation
          char const separator: No description
        
        Returns
          void: No description
        """
    def saveMacroscopicObservables(self, filename: str, separator: str = ';') -> None:
        """
        Description
        Save the main macroscopic observables in csv format.
        
        Args
          const std::string & filename: The name of the file 
          char const separator: The separator character (default is ';')
        
        Returns
          void: No description
        """
    def saveOutputStreetCounts(self, filename: str, reset: bool = False, separator: str = ';') -> None:
        """
        Description
        Save the street output counts in csv format.
        
        Args
          const std::string & filename: The name of the file 
          bool reset: If true, the output counts are cleared after the computation
          char const separator: No description
        
        Returns
          void: No description
        """
    def saveStreetDensities(self, filename: str, normalized: bool = True, separator: str = ';') -> None:
        """
        Description
        Save the street densities in csv format.
        
        Args
          const std::string & filename: The name of the file 
          bool normalized: If true, the densities are normalized in [0, 1] 
          char const separator: No description
        
        Returns
          void: No description
        """
    def saveTravelData(self, filename: str, reset: bool = False) -> None:
        """
        Description
        Save the travel data of the agents in csv format. 
        The file contains the following columns:
        
        Args
          const std::string & filename: The name of the file 
          bool reset: If true, the travel speeds are cleared after the computation 
        
        Returns
          void: No description
        """
    def setDataUpdatePeriod(self, dataUpdatePeriod: typing.SupportsInt) -> None:
        """
        Description
        Set the data update period.
        
        Args
          delay_t dataUpdatePeriod: delay_t, The period
        
        Returns
          void: No description
        """
    @typing.overload
    def setDestinationNodes(self, destinationNodes: collections.abc.Sequence[typing.SupportsInt]) -> None:
        """
        Description
        Set the destination nodes.
        
        Args
          typename TContainer: No description
          TContainer const & destinationNodes: A container of destination nodes ids
        
        Returns
          void: No description
        """
    @typing.overload
    def setDestinationNodes(self, destinationNodes: typing.Annotated[numpy.typing.ArrayLike, numpy.uint64]) -> None:
        """
        Description
        Set the destination nodes.
        
        Args
          typename TContainer: No description
          TContainer const & destinationNodes: A container of destination nodes ids
        
        Returns
          void: No description
        """
    @typing.overload
    def setDestinationNodes(self, destinationNodes: collections.abc.Mapping[typing.SupportsInt, typing.SupportsFloat]) -> None:
        """
        Description
        Set the destination nodes.
        
        Args
          typename TContainer: No description
          TContainer const & destinationNodes: A container of destination nodes ids
        
        Returns
          void: No description
        """
    def setErrorProbability(self, errorProbability: typing.SupportsFloat) -> None:
        """
        Description
        Set the error probability.
        
        Args
          double errorProbability: The error probability 
        
        Returns
          void: No description
        """
    def setForcePriorities(self: ..., forcePriorities: bool) -> None:
        """
        Description
        Set the force priorities flag.
        
        Args
          bool forcePriorities: The flag
        
        Returns
          void: No description
        """
    @typing.overload
    def setInitTime(self, timeEpoch: typing.SupportsInt) -> None:
        """
        Description
        Set the initial time as epoch time.
        
        Args
          std::time_t timeEpoch: The initial time as epoch time 
        
        Returns
          void: No description
        """
    @typing.overload
    def setInitTime(self, datetime: typing.Any) -> None:
        """
        Description
        Set the initial time as epoch time.
        
        Args
          std::time_t timeEpoch: The initial time as epoch time 
        
        Returns
          void: No description
        """
    def setMaxDistance(self, maxDistance: typing.SupportsFloat) -> None:
        """
        Description
        Set the maximum distance which a random agent can travel.
        
        Args
          double const maxDistance: The maximum distance 
        
        Returns
          void: No description
        """
    def setMaxTravelTime(self, maxTravelTime: typing.SupportsInt) -> None:
        """
        Description
        Set the maximum travel time which a random agent can travel.
        
        Args
          std::time_t const maxTravelTime: The maximum travel time 
        
        Returns
          void: No description
        """
    @typing.overload
    def setOriginNodes(self, originNodes: collections.abc.Mapping[typing.SupportsInt, typing.SupportsFloat]) -> None:
        """
        Description
        No description available.
        
        Args
          std::unordered_map< Id, double > const & originNodes: No description
        
        Returns
          void: No description
        """
    @typing.overload
    def setOriginNodes(self, originNodes: typing.Annotated[numpy.typing.ArrayLike, numpy.uint64]) -> None:
        """
        Description
        No description available.
        
        Args
          std::unordered_map< Id, double > const & originNodes: No description
        
        Returns
          void: No description
        """
    def setWeightFunction(self, weightFunction: PathWeight, weightThreshold: typing.SupportsFloat | None = None) -> None:
        ...
    def time(self) -> int:
        """
        Description
        Get the current simulation time as epoch time.
        
        Args
          None
        
        Returns
          std::time_t: std::time_t, The current simulation time as epoch time 
        """
    def time_step(self) -> int:
        """
        Description
        Get the current simulation time-step.
        
        Args
          None
        
        Returns
          std::time_t: std::time_t, The current simulation time-step 
        """
    def turnCounts(self) -> dict:
        """
        Description
        Get the turn counts of the agents.
        
        Args
          None
        
        Returns
          std::unordered_map< Id, std::unordered_map< Id, size_t > > const &: const std::unordered_map<Id, std::unordered_map<Id, size_t>>& The turn counts. The outer map's key is the street id, the inner map's key is the next street id and the value is the number of counts 
        """
    def updatePaths(self) -> None:
        """
        Description
        Update the paths of the itineraries based on the given weight function.
        
        Args
          None
        
        Returns
          void: No description
        """
class Itinerary:
    def __init__(self, id: typing.SupportsInt, destination: typing.SupportsInt) -> None:
        """
        Description
        No description available.
        
        Args
          const Itinerary: No description
        
        Returns
          void: No return value
        """
    def destination(self) -> int:
        """
        Description
        Get the itinerary's destination.
        
        Args
          None
        
        Returns
          Id: Id, The itinerary's destination 
        """
    def id(self) -> int:
        """
        Description
        Get the itinerary's id.
        
        Args
          None
        
        Returns
          Id: Id, The itinerary's id 
        """
    def setPath(self, path: collections.abc.Mapping[typing.SupportsInt, collections.abc.Sequence[typing.SupportsInt]]) -> None:
        """
        Description
        Set the itinerary's path.
        
        Args
          std::unordered_map< Id, std::vector< Id > > path: An adjacency matrix made by a 
        
        Returns
          void: No description
        """
class LogLevel:
    """
    Members:
    
      TRACE
    
      DEBUG
    
      INFO
    
      WARN
    
      ERROR
    
      CRITICAL
    
      OFF
    """
    CRITICAL: typing.ClassVar[LogLevel]  # value = <LogLevel.CRITICAL: 5>
    DEBUG: typing.ClassVar[LogLevel]  # value = <LogLevel.DEBUG: 1>
    ERROR: typing.ClassVar[LogLevel]  # value = <LogLevel.ERROR: 4>
    INFO: typing.ClassVar[LogLevel]  # value = <LogLevel.INFO: 2>
    OFF: typing.ClassVar[LogLevel]  # value = <LogLevel.OFF: 6>
    TRACE: typing.ClassVar[LogLevel]  # value = <LogLevel.TRACE: 0>
    WARN: typing.ClassVar[LogLevel]  # value = <LogLevel.WARN: 3>
    __members__: typing.ClassVar[dict[str, LogLevel]]  # value = {'TRACE': <LogLevel.TRACE: 0>, 'DEBUG': <LogLevel.DEBUG: 1>, 'INFO': <LogLevel.INFO: 2>, 'WARN': <LogLevel.WARN: 3>, 'ERROR': <LogLevel.ERROR: 4>, 'CRITICAL': <LogLevel.CRITICAL: 5>, 'OFF': <LogLevel.OFF: 6>}
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class Measurement:
    def __init__(self, mean: typing.SupportsFloat, std: typing.SupportsFloat) -> None:
        """
        Description
        No description available.
        
        Args
          std::span< T > data: No description
        
        Returns
          void: No return value
        """
    @property
    def mean(self) -> float:
        """
        Description
        No description available.
        
        Args
          None
        
        Returns
          void: No return value
        """
    @mean.setter
    def mean(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def std(self) -> float:
        """
        Description
        No description available.
        
        Args
          None
        
        Returns
          void: No return value
        """
    @std.setter
    def std(self, arg0: typing.SupportsFloat) -> None:
        ...
class PathWeight:
    """
    Members:
    
      LENGTH
    
      TRAVELTIME
    
      WEIGHT
    """
    LENGTH: typing.ClassVar[PathWeight]  # value = <PathWeight.LENGTH: 0>
    TRAVELTIME: typing.ClassVar[PathWeight]  # value = <PathWeight.TRAVELTIME: 1>
    WEIGHT: typing.ClassVar[PathWeight]  # value = <PathWeight.WEIGHT: 2>
    __members__: typing.ClassVar[dict[str, PathWeight]]  # value = {'LENGTH': <PathWeight.LENGTH: 0>, 'TRAVELTIME': <PathWeight.TRAVELTIME: 1>, 'WEIGHT': <PathWeight.WEIGHT: 2>}
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class RoadNetwork:
    @typing.overload
    def __init__(self) -> None:
        """
        Description
        Construct a new
        
        Args
          AdjacencyMatrix adj: An adjacency matrix made by a 
        
        Returns
          void: No return value
        """
    @typing.overload
    def __init__(self, arg0: AdjacencyMatrix) -> None:
        """
        Description
        Construct a new
        
        Args
          AdjacencyMatrix adj: An adjacency matrix made by a 
        
        Returns
          void: No return value
        """
    def adjustNodeCapacities(self) -> None:
        """
        Description
        Adjust the nodes' transport capacity. 
        The nodes' capacity is adjusted using the graph's streets transport capacity, which may vary basing on the number of lanes. The node capacity will be set to the sum of the incoming streets' transport capacity.
        
        Args
          None
        
        Returns
          void: No description
        """
    def autoMapStreetLanes(self) -> None:
        """
        Description
        Automatically re-maps street lanes basing on network's topology. 
        For example, if one street has the right turn forbidden, then the right lane becomes a straight one
        
        Args
          None
        
        Returns
          void: No description
        """
    def capacity(self) -> int:
        """
        Description
        Get the maximum agent capacity.
        
        Args
          None
        
        Returns
          auto: unsigned long long The maximum agent capacity of the graph 
        """
    def exportEdges(self, fileName: str) -> None:
        """
        Description
        Export the graph's edges to a csv-like file separated with ';'.
        
        Args
          const std::string & fileName: No description
        
        Returns
          void: No description
        """
    def exportNodes(self, fileName: str) -> None:
        """
        Description
        Export the graph's nodes to a csv-like file separated with ';'.
        
        Args
          const std::string & fileName: No description
        
        Returns
          void: No description
        """
    def importCoordinates(self, fileName: str) -> None:
        """
        Description
        Import the graph's nodes from a file.
        
        Args
          const std::string & fileName: The name of the file to import the nodes from. 
        
        Returns
          void: No description
        """
    @typing.overload
    def importEdges(self, fileName: str) -> None:
        """
        Description
        Import the graph's streets from a file.
        
        Args
          typename... TArgs: No description
          const std::string & fileName: The name of the file to import the streets from.
          TArgs &&... args: No description
        
        Returns
          void: No description
        """
    @typing.overload
    def importEdges(self, fileName: str, separator: str) -> None:
        """
        Description
        Import the graph's streets from a file.
        
        Args
          typename... TArgs: No description
          const std::string & fileName: The name of the file to import the streets from.
          TArgs &&... args: No description
        
        Returns
          void: No description
        """
    @typing.overload
    def importEdges(self, fileName: str, bCreateInverse: bool) -> None:
        """
        Description
        Import the graph's streets from a file.
        
        Args
          typename... TArgs: No description
          const std::string & fileName: The name of the file to import the streets from.
          TArgs &&... args: No description
        
        Returns
          void: No description
        """
    def importMatrix(self, fileName: str, isAdj: bool = True, defaultSpeed: typing.SupportsFloat = 13.8888888889) -> None:
        """
        Description
        Import the graph's adjacency matrix from a file. If the file is not of a supported format, it will read the file as a matrix with the first two elements being the number of rows and columns and the following elements being the matrix elements.
        
        Args
          const std::string & fileName: The name of the file to import the adjacency matrix from. 
          bool isAdj: A boolean value indicating if the file contains the adjacency matrix or the distance matrix. 
          double defaultSpeed: The default speed limit for the streets 
        
        Returns
          void: No description
        """
    def importNodeProperties(self, fileName: str, separator: str = ';') -> None:
        """
        Description
        Import the graph's nodes properties from a file.
        
        Args
          typename... TArgs: No description
          const std::string & fileName: The name of the file to import the nodes properties from.
          TArgs &&... args: No description
        
        Returns
          void: No description
        """
    def importTrafficLights(self, fileName: str) -> None:
        """
        Description
        Import the graph's traffic lights from a file.
        
        Args
          const std::string & fileName: The name of the file to import the traffic lights from.
        
        Returns
          void: No description
        """
    def initTrafficLights(self, minGreenTime: typing.SupportsInt = 30) -> None:
        """
        Description
        Initialize the traffic lights with random parameters.
        
        Args
          Delay const minGreenTime: The minimum green time for the traffic lights cycles (default is 30)
        
        Returns
          void: No description
        """
    def makeRoundabout(self, id: typing.SupportsInt) -> None:
        """
        Description
        Convert an existing node into a roundabout.
        
        Args
          Id nodeId: The id of the node to convert to a roundabout 
        
        Returns
          Roundabout: A reference to the roundabout 
        """
    def makeSpireStreet(self, id: typing.SupportsInt) -> None:
        """
        Description
        Convert an existing street into a spire street.
        
        Args
          Id streetId: The id of the street to convert to a spire street 
        
        Returns
          void: No description
        """
    def makeTrafficLight(self, id: typing.SupportsInt, cycleTime: typing.SupportsInt, counter: typing.SupportsInt) -> None:
        """
        Description
        Convert an existing node to a traffic light.
        
        Args
          Id const nodeId: The id of the node to convert to a traffic light 
          Delay const cycleTime: The traffic light's cycle time 
          Delay const counter: The traffic light's counter initial value. Default is 0 
        
        Returns
          TrafficLight: A reference to the traffic light 
        """
    def nCoils(self) -> int:
        """
        Description
        Get the graph's number of coil streets.
        
        Args
          None
        
        Returns
          Size: The number of coil streets 
        """
    def nEdges(self) -> int:
        """
        Description
        Get the number of edges.
        
        Args
          None
        
        Returns
          size_t: size_t The number of edges 
        """
    def nIntersections(self) -> int:
        """
        Description
        Get the graph's number of intersections.
        
        Args
          None
        
        Returns
          Size: The number of intersections 
        """
    def nNodes(self) -> int:
        """
        Description
        Get the number of nodes.
        
        Args
          None
        
        Returns
          size_t: size_t The number of nodes 
        """
    def nRoundabouts(self) -> int:
        """
        Description
        Get the graph's number of roundabouts.
        
        Args
          None
        
        Returns
          Size: The number of roundabouts 
        """
    def nTrafficLights(self) -> int:
        """
        Description
        Get the graph's number of traffic lights.
        
        Args
          None
        
        Returns
          Size: The number of traffic lights 
        """
class TrafficLightOptimization:
    """
    Members:
    
      SINGLE_TAIL
    
      DOUBLE_TAIL
    """
    DOUBLE_TAIL: typing.ClassVar[TrafficLightOptimization]  # value = <TrafficLightOptimization.DOUBLE_TAIL: 1>
    SINGLE_TAIL: typing.ClassVar[TrafficLightOptimization]  # value = <TrafficLightOptimization.SINGLE_TAIL: 0>
    __members__: typing.ClassVar[dict[str, TrafficLightOptimization]]  # value = {'SINGLE_TAIL': <TrafficLightOptimization.SINGLE_TAIL: 0>, 'DOUBLE_TAIL': <TrafficLightOptimization.DOUBLE_TAIL: 1>}
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
def get_log_level() -> LogLevel:
    """
    Get the current global log level
    """
def set_log_level(level: LogLevel) -> None:
    """
    Set the global log level for spdlog
    """
CRITICAL: LogLevel  # value = <LogLevel.CRITICAL: 5>
DEBUG: LogLevel  # value = <LogLevel.DEBUG: 1>
DOUBLE_TAIL: TrafficLightOptimization  # value = <TrafficLightOptimization.DOUBLE_TAIL: 1>
ERROR: LogLevel  # value = <LogLevel.ERROR: 4>
INFO: LogLevel  # value = <LogLevel.INFO: 2>
LENGTH: PathWeight  # value = <PathWeight.LENGTH: 0>
OFF: LogLevel  # value = <LogLevel.OFF: 6>
SINGLE_TAIL: TrafficLightOptimization  # value = <TrafficLightOptimization.SINGLE_TAIL: 0>
TRACE: LogLevel  # value = <LogLevel.TRACE: 0>
TRAVELTIME: PathWeight  # value = <PathWeight.TRAVELTIME: 1>
WARN: LogLevel  # value = <LogLevel.WARN: 3>
WEIGHT: PathWeight  # value = <PathWeight.WEIGHT: 2>
__version__: str = '3.12.1'
