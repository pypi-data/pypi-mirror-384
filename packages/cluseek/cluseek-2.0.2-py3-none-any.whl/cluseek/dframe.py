import gc
import re
from collections import Counter
import enum

# This file describes most of the common classes used to store
#   the data being processed.


# * * * Front/Nucleotide Tree
# These classes describe the position of a given nucleotide sequence
#  EG. CodingSequence1 is on Scaffold5, which is a sequence from Taxon319's genome
#
# When adding elements to the data structure without calling the constructor, 
#   always use the add_[element] method to add elements lower in the hierarchy 
#   to ensure interconnectedness.

# DELETE LATER
#class Strand(enum.Enum):
#    PRIMARY = "+"
#    COMPLEMENTARY = "-" #This is the reverse complement
#    BOTH = "0" #This is the default if you don't care about strandedness
    

class Root():
    def __init__(self):
        super().__init__()
        self.txAll  = {}
        self.scAll  = {}
        self.ptAll  = {}
        self.iptAll = {}
    def ptAll(self):
        ptAll = {}
        for ipt in sself.iptAll.values():
            ptAll.update(ipt.pts)
        return(ptAll)
class Taxon():
    #sciname_pattern = re.compile(r"(?P<genus>\[?[a-zA-Z0-9]+\[?)( (?P<species>([Ss]p. )?[a-zA-Z0-9]+))?( (?P<strain>.+))?")
    sciname_pattern = re.compile(
        r"([Uu]ncultured )?([Cc]andidatus )?(\[?(?P<genus>[A-Z][a-z]+)\]?) (?P<species>([Ss]p\.)|([a-z]+)).*")
    
    # These words denote that a sequence is definetly -not-
    #   a standard scientific name.
    naughty_words = [
        r"([A-Z][a-z]+) bacterium( .*)",
    ]
    naughty_words = [re.compile(naughty) for naughty in naughty_words]
    def __init__(self, taxid, root, strain, sciname=None):
        super().__init__()
        # * Non-args
        self.scs = {}
        # * Mandatory args
        self.taxid = taxid
        self.strain = strain
        self.root = root
        self.root.txAll[self.taxstrid] = self
        # * Optional args
        self.sciname = sciname
        
        
        match = re.match(self.sciname_pattern, self.sciname)
        naughties = [re.match(naughty, self.sciname) for naughty in self.naughty_words]
        if (match is None and sciname) or any(naughties):
            print(f"Failed matching sciname: {self.sciname}")
            self.genus = None
            self.species = None
        else:
            self.genus = match["genus"]
            self.species = match["species"]
        #print(self.sciname)
        #print(f"{self.genus} {self.species} * * * {self.strain}")
        #print("")
        #self.strain = strain
    @property
    def taxstrid(self):
        return(f"{self.taxid}:{self.strain}")
    def add_scaffold(self, scaffold):
        if scaffold.accession in self.scs:
            print(f"WARNING: Scaffold {scaffold} already in taxon {scaffold.tx}. Overwriting...")
        self.scs[scaffold.accession] = scaffold
        scaffold.tx = self
class Scaffold():
    #Roughly corresponds to a genbank sequence record
    def __init__(self, accession, taxon, version):
        super().__init__()
        # * Non-args
        self.fts = {}
        self.version = version
        self.tx = None
        
        self.annotations = None
        # * Mandatory args
        assert "." not in accession
        self.accession = accession
        self.version = version
        taxon.add_scaffold(self)
        self.tx.root.scAll[self.accession] = self
    #def __repr__(self):
    #    pass
    #def __str__(self):
    #    pass
    pass
class Feature():
    #Sequence feature, attached to a Sequence Record
    def __init__(self, scaffold, reference, start, stop, fttype, strand, attach=True):
        super().__init__()
        # * Non-args
        # * Mandatory args
        self.start = start
        self.stop  = stop
        assert fttype in ("cds", "genecluster")
        self.type  = fttype #Possible values: "cds", "genecluster"
        
        assert strand in ("+", "-", "0"), "Strand not specified for a coding sequence!"
        self.strand = strand
        
        #The only real way of hooking up sc/refs right now        
        #TODO: The following will break horribly if a non-accession 
        #   element is referred to by a feature.
        #   Possibly use an "add_as_feature()" method that 
        #   adds features implicitly.
        self.sc    = scaffold
        self.ref   = reference
        if attach:
            self.sc.fts[self.ref.accession] = self
            self.ref.fts[self.sc.accession] = self
        # * Optional args
        pass
    def __repr__(self):
        return("Feature ({}) from {} to {} on {}".format(
                                                self.type,
                                                self.start, 
                                                self.stop, 
                                                self.sc.accession))
    def __str__(self):
        return("Feature ({}) from {} to {} on {}".format(
                                                self.type,
                                                self.start, 
                                                self.stop, 
                                                self.sc.accession))
    def is_inside(self, ft):
        #Check if this feature is inside another feature
        #This is useful when we use features to define regions
        if self.sc is not ft.sc:
            print("Error: Features {} and {} are not on the same scaffold!")
            return(None)
        if ((ft.start <= self.start) and (ft.stop >= self.stop)):
            #"If the other feature starts sooner and ends later"
            return(True)
        else:
            return(False)
    def overlaps(self, ft):
        #Returns True of features overlap
        if self.sc is not ft.sc:
            print("Error: Features {} and {} are not on the same scaffold!")
            return(None)
        if ((self.start <= ft.stop <= self.stop)
          or (ft.start <= self.stop <= ft.stop)):
            #If the stop of either feature is within the bounds
            #of the other, they're overlapped.
            return(True)
    def distance_from(self, ft):
        #Calculates distance between features.
        if self.overlaps(ft):
            return(None)
        #We don't need to do a check if the features are on the
        # same scaffold, because self.overlaps() already does that.
        #
        d1 = ft.start - self.stop
        d2 = self.start - ft.stop
        #If the features aren't overlapping, either d1 or d2 will
        # be negative.
        return(max(d1, d2))
    def length(self):
        return(self.stop-self.start+1)
# Search Result
class GeneticRegion(Feature):
    def __init__(self, scaffold, start, stop, hit_score=None, seq=None):
       # Initialize the superclasss.   
       #    We'll be using attach=False until/unless
       #    an AbstractGeneCluster class gets written
       #    to track multiple instances of the same
       #    cluster (eg. APD cluster in multiple species)
        super().__init__(scaffold=scaffold, start=start, strand="0",
                         stop=stop, reference=self, fttype="genecluster",
                         attach=False)
        self.hit_score = hit_score
        self.seq = seq
    @property
    def fts(self):
        fts = {}
        for ftname in self.sc.fts:
            ft = self.sc.fts[ftname]
            if ft.is_inside(self):
                fts[ftname] = ft
        return(fts)
# * * * Back/Protein Tree
# These classes help cover the relationship between peptide
#  sequences -- identical proteins, homologous proteins, etc.
#  
# Included are also other classes like Regions -- all share
# the trait of being linked from the main tree through Feature.ref
class Protein():
    def __init__(self, accession, version, iprotein, seq=None, name=None, type=None):
        super().__init__()
        # *Non-arguments
        self.fts   = {}   # Coding sequences
        self.homs  = []   # Homologies to
        self.qhoms = []   # Homologies 
        self.ipt   = None #Declaring var
        self.cluster = None #Declaring var
        # *Mandatory args
        assert "." not in accession
        self.accession = accession # GenBank Accession
        self.version = version # Accession version 
        #                      #(normally separated from accession by period)
        iprotein.add_protein(self)
        self.ipt.root.ptAll[self.accession] = self
        # *Optional args
        self.name  = name # (Slightly more) human-readable name
        self.type  = type # Description, usually from GenBank
        self.seq   = seq  # Amino acid sequence
    def __repr__(self):
        return(f"Protein {self.accession}, {self.type}, {self.name}")
    def __str__(self):
        return(self.__repr__())
    #def __repr__(self):
    #    pass
    #def __str__(self):
    #    pass
    pass
class IdenticalProteinSet():
    #Roughly corresponds to the genbank ipg record
    def __init__(self, accession, root, proteins=[]):
        super().__init__()
        # *Non-args
        self.pts = {}
        #fts - features are generated via self.fts()
        # *Mandatory arguments
        self.accession = accession
        self.root = root
        if self.accession in self.root.iptAll:
            print("WARNING: iProtein {} already in root, overwriting...".format(self.accession))
        self.root.iptAll[self.accession] = self
        # *Optional args
        for pt in proteins:
            self.add_protein(pt)
    def add_protein(self, protein):
        if protein.accession in self.pts:
            print("WARNING: Protein {} already in iProtein {}, overwriting...".format(protein.accession, self.accession))
        self.pts[protein.accession] = protein
        protein.ipt = self
    def fts(self):
        #TODO: DEPRICATED
        #Inaccurate if there are multiple instances of the same protein on the same scaffold.
        #It shouldn't really be possible normally, but hacking things opens it to bugs
        #TODO: return an iterator instead of a dict, that's the only way
        myFeatures = {}
        for pt in self.pts.values():
            myFeatures.update(pt.fts)
        return(myFeatures)
    def __getitem__(self,item):
        return(self.pts[item])
    def __contains__(self,item):
        return(item in self.pts)
    #def __repr__(self):
    #    pass
    #def __str__(self):
    #    pass
    pass
#
class ReferenceDummy():
    def __init__(self):
        super().__init__()
        self.accession = None
        self.fts = {}
    def __repr__(self):
        return("ReferenceDummy")
    def __str__(self):
#

        return("ReferenceDummy")


# Classes for protein clustering

class ProteinClusterHierarchy():
    def __init__(self, root, global_clustering_criteria=None, local_clustering_criteria=None):
        super().__init__()
        self.global_clustering_identity = global_clustering_criteria
        self.local_clustering_criteria = local_clustering_criteria
        
        self.root = root
        self.graph = None
        
        self.clusters = {} # Only toplevel (parentless) clusters
        self.clusters_all = {} # Includes child clusters
        self.member_to_supercluster = {}
        self.member_to_subcluster = {}
        self.local_groups = {}
        
        self.highest_numerical_index = -1
    
    def set_graph(self, graph):
        self.graph = graph
    def get_all_local_groups(self):
        local_groups = {}
        for cluster in self.clusters_all.values():
            if not cluster.local_group: continue
            if cluster.local_group not in local_groups:
                local_groups[cluster.local_group] = set()
            local_groups[cluster.local_group].add(cluster)
        return(local_groups)
    def get_local_groups(self, id_):
        return(self.get_all_local_groups()[id_])
    
    def assign_to_local_group(self, cluster, group_id):
        if group_id not in self.local_groups:
            self.local_groups[group_id] = []
        self.local_groups[group_id].append(cluster)
    # = = Cluster creation/removal = =
    def get_or_create(self, id_, **kwargs):
        # Retrieves or generates a cluster based on ID
        try:
            if int(id_) > self.highest_numerical_index:
                self.highest_numerical_index = int(id_)
        except:
            pass
        
        id_ = str(id_)
        
        if id_ not in self.clusters:
            #print(f"Making cluster {id_}")
            cluster = ProteinCluster(id_, self, **kwargs)
            self._register_new_cluster(cluster)
            return(cluster)
        else:
            return(self.clusters[id_])
    def new_cluster(self, **kwargs):
        # Generates a cluster with an automatically assigned ID
        self.highest_numerical_index += 1
        cluster = ProteinCluster(
            id_=str(self.highest_numerical_index), 
            hierarchy=self, 
            **kwargs)
        self._register_new_cluster(cluster)
        return(cluster)
    def _register_new_cluster(self, cluster):
        assert cluster.id_ not in self.clusters_all, "Cluster ID already exists."
        assert len(cluster.proteins) == 0, ("Cannot register cluster with proteins "
                                            "already assigned to it.")
        self.clusters_all[cluster.id_] = cluster
        if cluster._parent is None:
            self.clusters[cluster.id_] = cluster
        
        self.on_new_cluster_registered(cluster)
    def on_new_cluster_registered(self, cluster):
        pass
    def remove_cluster(self, cluster):
        # To be overwritten.
        self._remove_cluster(cluster)

    def _remove_cluster(self, cluster):
        print(f"Removing {cluster.id_}...")
        cluster.removed = True
        del self.clusters_all[cluster.id_]
        if cluster._parent is None:
            del self.clusters[cluster.id_]
    # = = Protein management = =
    def add_protein(self, protein, cluster_id, is_centroid=False, **kwargs):
        # Used to add a brand new protein that isn't in the hierarchy yet
        # Cluster must be pre-created
        cluster = self.clusters_all[cluster_id]
        
        cluster.proteins[protein.accession] = protein
        self._register_protein(protein, cluster)
        self._assign_protein(protein, cluster)
        
        if is_centroid:
            assert cluster.centroid is None
            cluster.centroid = protein
    def _register_protein(self, protein, cluster):
        assert len(cluster.subclusters) == 0, "Cannot register protein to a supercluster"
        self.member_to_subcluster[protein.accession] = cluster
    def _assign_protein(self, protein, cluster):
        assert isinstance(protein, Protein), "Only accepts proteins"
        self.member_to_supercluster[protein.accession] = cluster

class ProteinCluster():
    def __init__(self, id_, hierarchy, type_, hidden=False):
        super().__init__()
        
        # Certain properties are stored in this dict for save file
        #   compatibility. Eventually I'd like to migrate all 
        #   saved variables here, for now this is only partial.
        self._metadata = {
            "local_group": None}
        
        self.id_ = id_ # String of a number
        #can be "locally_aligned", "globally_aligned", "user_defined",
        #        "community_based"
        self.set_type(type_)
        self.hierarchy = hierarchy
        
        self._parent = None
        self.local_group = None
        
        self.proteins = {}
        self.subclusters = {}
        # Only applicable for globally aligned clusters
        self.centroid = None
        
        self.removed = False
    @property
    def local_group(self):
        return(self._metadata["local_group"])
    @local_group.setter
    def local_group(self, new_value):
        self._metadata["local_group"] = new_value
    def get_bottomlevel_subclusters(self):
        bottomlevels = set()
        to_check = [self]
        
        for cluster in to_check:
            if cluster.subclusters:
                to_check.extend(list(cluster.subclusters.values()))
            else:
                bottomlevels.add(cluster)
        return(bottomlevels)
    def get_local_groups(self):
        if not self.subclusters:
            return({self.local_group})
        else:
            return({subcluster.local_group for subcluster \
                    in self.get_bottomlevel_subclusters()})
    def get_related_clusters(self):
        # Returns local groups of self or all subclusters.
        # Will give results even for heterogenous clusters
        #   assembled by people who think they know better
        #   than the clustering process (which they might).
        to_check = [self]
        local_group_ids = set()
        
        for cluster in to_check:
            if cluster.subclusters:
                to_check.extend(list(cluster.subclusters.values()))
            elif cluster.local_group is not None:
                # Not all globally_aligned clusters have a local group sadly
                assert cluster.local_group is not None
                local_group_ids.add(cluster.local_group)
        
        related_clusters = set()
        for local_group_id in local_group_ids:
            related_clusters |= set(self.hierarchy.local_groups[local_group_id])
        
        return(related_clusters)
    def _get_composition(self):
        composition = Counter()
        for protein in self.proteins.values():
            composition[protein.type] += 1
        return(composition)
    def set_local_group(self, group_id):
        self.local_group = group_id
        self.hierarchy.assign_to_local_group(self, group_id)
    def set_type(self, value):
        assert value in {"locally_aligned", "globally_aligned", "user_defined", "community_based", "marker"}
        self.type_ = value
    def add_subcluster(self, subcluster):
        assert subcluster._parent is None
        if self.type_ == "globally_aligned":
            raise Exception("Cannot add subclusters to globally_aligned clusters.")
        
        # Assign subcluster
        subcluster._set_parent(self)
        self.subclusters[subcluster.id_] = subcluster
        del self.hierarchy.clusters[subcluster.id_]
        
        # Assign subcluster's protein to all clusters above it
        #   in the hierarchy
        for cluster in self.get_lineage():
            cluster.proteins.update(subcluster.proteins)
        
        # Assign the subcluster's proteins to the toplevel cluster
        superparent = self.get_toplevel()
        for protein in subcluster.proteins.values():
            self.hierarchy._assign_protein(protein, superparent)
    def remove_subcluster(self, subcluster):
        # Unassign subcluster
        subcluster._set_parent(None)
        self.hierarchy.clusters[subcluster.id_] = subcluster
        del self.subclusters[subcluster.id_]
        
        # Remove subcluster's proteins from the clusters that
        #   inherited them from subcluster
        for cluster in self.get_lineage():
            for protein_accession in subcluster.proteins.keys():
                try:
                    del self.proteins[protein_accession]
                except KeyError as e:
                    print(f"WARNING: Invalid protein accession {protein_accession}.")
                    print(f"\tProtein in clustering result: {protein_accession in self.hierarchy.member_to_subcluster}")
        
        # Assign the subcluster's proteins back to it from toplevel
        for protein in subcluster.proteins.values():
            self.hierarchy._assign_protein(protein, subcluster)
    def do_remove_check(self):
        if len(self.proteins) == 0:
            self.hierarchy.remove_cluster(self)
    def _set_parent(self, parent):
        self._parent = parent
    def get_lineage(self):
        parents = []
        parents.append(self)
        if self._parent:
            parents.extend(self._parent.get_lineage())
        return(parents)
    def get_toplevel(self):
        if self._parent:
            return(self._parent.get_toplevel())
        else:
            return(self)