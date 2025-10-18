

#TODO:
#    Make a local-alignment based clustering algorithm that
#    1.  Splits the sequences into smaller non-homogenous groups
#    2.  Aligns the sequences and tries to establish clear clusters
#        - Either via length checking or motif checking
#        - Maybe compare k-mers? I dunno.



from Bio.Blast import NCBIXML
from Bio.Blast import NCBIWWW
import xml.etree.ElementTree as ET
from Bio import Entrez
import gzip
import bz2
import math
import time
import os
import sys
import re
import io
import sqlite3 as sql
import pkg_resources
#import sys
import threading
import trace
import zlib
import tempfile
import json
import networkx as nx

from Bio import SeqIO, SeqFeature, Seq

from cluseek import dframe
# I'd prefer not to import uiqt, but it is effectively necessary for neighborhood saving
from cluseek import uiqt


import subprocess

#Debug
from collections import Counter

#Debug2
import code
#code.interact(local=locals())

#TODO: Set user's email, and config the slee+p between tries
#NOTE: When downloading neighbourhoods, a failure results in waiting 340s
#      although the average time to download a gb is at most 2s 
#      (at least on this machine)
#      (Why are we waiting this long? It's kind of inconvenient.)
Entrez.email = "cluseek@biomed.cas.cz"
Entrez.sleep_between_tries=15

#For UI interactions, override this if necessary.

class InvalidFileTypeError(Exception):
    def __init__(self, message):
        super().__init__(message)

class DummyDownloadManager():
    # For integration with GUI. 
    # Override this class if you want dbdl to talk to 
    # the GUI about what's going on.
    # The methods below are called by functions in this
    # module to signal what's going on.
    def __init__(self):
        pass
    def download_starting(self, type, number_to_download):
        # type = What kind of data is being downloaded. 
        #        Valid so far: "IPG", "GB"
        # number_to_download = number of entries present locally,
        #                       which will need to be downloaded
        # False = Download is OK, proceed
        # True = Do not start download
        return False
    def download_status(self, number_left_to_download):
        # Same as before, but interrupts download.
        return False
    def download_ended(self):
        pass
    def is_aborted(self):
        pass
DOWNLOAD_MANAGER = DummyDownloadManager()
ERROR_MANAGER = None

class DatabaseManager():
    class DatabaseContextManager():
        def __init__(self, connection, lock):
            self.connection = connection
            self.cursor = None
            self.lock = lock
        def __enter__(self):
            self.lock.acquire()
            self.cursor = self.connection.cursor()
            return(self.cursor)
        def __exit__(self, exception, exc_value, exc_traceback):
            self.cursor.close()
            if not exception:
                self.connection.commit()
            self.lock.release()
    #TODO: Update the last_data_added entry in metadata
    #      each time data is downloaded
    def __init__(self):
        self.metadata = None
        self.offline = None
        self.temp_db_path = ":memory:"
        self.opened_db_path = None
        
        self.active_db_connection = None
        self.active_db_lock = threading.Lock()
    
    # = = Core Methods = =
    def open_old_db(self, path):
        if os.path.isfile(path):
            db_to_load_connection = self.check_db(path)
        else:
            self.on_error_is_not_file("Path specified is not a file.")
            return(False)
        
        if db_to_load_connection is None:
            print("... Failed to open database.")
            return False
        print(f"Valid existing DB checked at {path}")
        
        assert self.temp_db_path
        if os.path.isfile(self.temp_db_path):
            raise FileExistsError(
                "Cannot create temporary database in path specified.")
        self.active_db_connection = sql.connect(
            self.temp_db_path, 
            check_same_thread=False)
        
        db_to_load_connection.backup(self.active_db_connection)
        self.opened_db_path = path
        
        return True
    def open_new_db(self):
        if os.path.isfile(self.temp_db_path):
            raise FileExistsError(
                "Cannot create temporary database in path specified.")
        
        connection = self.new_db(self.temp_db_path)
        
        if connection is None:
            print("... Failed to create new database.")
            return False
        
        self.active_db_connection = connection
        return True
    def check_db(self, path):
        # Connects a db, making checks as to its validity.
        # Returns either connection or None
        
        # Check if path points to file
        if not os.path.isfile(path):
            #raise FileNotFoundError("Invalid db path.")
            print("Invalid database path.")
            self.on_error_invalid_path()
            return None
        
        failed = True
        connection = None
        cursor = None
        try:
            # Open connection
            connection = sql.connect(path, check_same_thread=False)
            cursor = connection.cursor()
            
            # Extract data
            rows = cursor.execute("SELECT key,value FROM cluseek_metadata").fetchall()
            metadata = {}
            for row in rows:
                metadata[row[0]] = row[1]
            
            # Check if this really is a save file
            if metadata.get("type") != "CluSeek Save File":
                raise InvalidFileTypeError("Not a CluSeek analysis file!")
            
            # Compare versions
            file_ver = metadata["version"].split(".")
            app_ver = str(pkg_resources.get_distribution("cluseek").version)\
                        .split(".")
            if file_ver[0] != app_ver[0] or file_ver[1] != file_ver[1]:
                self.on_error_different_version(
                    "This file was created in CluSeek version {'.'.join(file_ver)}, "
                    "while you are using CluSeek version '.'.join(app_ver)")
        except sql.DatabaseError:
            # Failed to open save file
            print("Error: File is not a SQLite database.")
            self.on_error_loading_file("File is not a SQLite database.")
        except (sql.OperationalError, InvalidFileTypeError):
            # Failed to open some part of the save file that should be there
            print("Error: File is not a valid CluSeek analysis file.")
            self.on_error_loading_file("File is not a valid CluSeek analysis file.")
        else:
            failed = False
        finally:
            if failed:
                if cursor: cursor.close()
                if connection: connection.close()
        if failed:
            return None
        else:
            return connection
    def get_cursor(self):
        if self.active_db_connection:
            return(
                self.DatabaseContextManager(
                    self.active_db_connection, 
                    self.active_db_lock))
    def new_db(self, path):
        try:
            # Create new db
            # returns connection, cursor
            # TODO: should also return None, None if db creation failed
            connection = sql.connect(path, check_same_thread=False)
            cursor = connection.cursor()
            
            # metadata table
            cursor.execute("CREATE TABLE cluseek_metadata(key, value)")
            metadata = (
                {"key": "type", "value": "CluSeek Save File"},
                {"key": "version", "value": str(pkg_resources.\
                    get_distribution("cluseek").version)},
                {"key": "created", "value": time.time()},
                {"key": "last_data_added", "value": time.time()},
            )
            cursor.executemany("INSERT INTO cluseek_metadata VALUES (:key, :value)",
                               metadata)
            
            # ipg features
            cursor.execute("CREATE TABLE ipgfeats(fttype, ftstart, ftstop, ftstrand, "
                                            "ptacc, ptver, ptname, iptacc, sciname, "
                                            "scacc, scver, taxid, taxstrain, time_added)")
            
            # GB sequences
            cursor.execute("CREATE TABLE gbseqs(accession, start, stop, "
                                               "data, time_added)")
            
            # Inputs (BLASTP XMLs)
            cursor.execute("CREATE TABLE blastpxml(xml)")
            
            # Neiview saves
            cursor.execute("CREATE TABLE neiview_clusters(nei_id, cluster_id, type_, "
                                                         "centroid, parent, proteins, "
                                                         "metadata, styledict)")
            cursor.execute("CREATE TABLE neiviews(nei_id, regions, config)")
            
            # Finish
            connection.commit()
        except Exception as e: raise e
        finally:
            cursor.close()
        return(connection)
    
    def save_active_to(self, path=None):
        print(f"Saving active to... {path}")
        if path is None:
            path = self.opened_db_path
        
        if os.path.isfile(path):
            try:
                os.remove(path)
            except:
                self.on_error_file_already_exists(
                    "Could not overwrite selected file.")
        
        self.active_db_lock.acquire()
        output_connection = sql.connect(path)
        try:
            self.active_db_connection.backup(output_connection)
        except Exception as e:
            raise e
        finally:
            output_connection.close()
            self.active_db_lock.release()
    
    def on_error_invalid_path(self, reason=None):
        print("Error: Invalid path")
    def on_error_loading_file(self, reason=None):
        print("Error: Failed to load file")
    def on_error_different_version(self, reason=None):
        print("Warning: Different version")
    def on_error_file_already_exists(self, reason=None):
        pass
    def on_error_is_not_file(self, reason=None):
        pass
    
    # = Status control
    def set_offline(self, offline):
        assert isinstance(offline, bool)
        self.offline = offline
        self.on_offline_changed()
    # Virtual function
    @staticmethod
    def on_offline_changed():
        pass
    
    # = = IPGFeature Methods = =
    def obtain_ipgs(self, keys):
        keys = set(keys) # This also prevents us from modifying the original list by accident
        keys_list = list(keys)
        download_thread = None
        work_thread = None
        _aborted = False
        
        local_keys = [x[0] for x in self._retrieve_ipgft_ids(
            protein_accessions=keys_list)]
        keys_to_download = keys.difference(local_keys)
        
        print(f"{len(keys_to_download)} keys missing, {len(local_keys)} found")
        
        # Ask download manager:
        _aborted = False
        if keys_to_download and not self.offline and not _aborted:
            print(f"{len(keys_to_download)} accessions not present locally, downloading...")
            
            downloaded_handle = [None]
            download_active = threading.Lock()
            
            chunk_size = 500
            chunks = [x for x in chunkify(list(keys_to_download), chunk_size)]
            
            
            _aborted = DOWNLOAD_MANAGER.download_starting(
                "protein", number_to_download=len(chunks))
            
            max_retries = 1
            retries = max_retries
            i = 0
            while i < len(chunks):
                chunk = chunks[i]
                def run():
                    print("Sending request")
                    # Executed by work thread
                    download_active.acquire()
                    handle = self._download_ipg_chunk(chunk)
                    downloaded_handle[0] = handle
                    download_active.release()
                work_thread = threading.Thread(target=run, daemon=True)
                work_thread.start()
                
                time.sleep(0.5)
                
                # Loop waiting for download to finish
                while download_active.locked():
                    time.sleep(1)
                    if DOWNLOAD_MANAGER.is_aborted():
                        _aborted = True
                        break
                        # We don't actually wait for the thread to finish.
                        # Just go with what we have already.
                        # The thread ought to quit on its own
                        # after downloading the next chunk.
                
                # After wait loop terminates:
                if _aborted:
                    break
                else:
                    try:
                        self.import_ipgxml(ipg_xml_handle=downloaded_handle[0])
                    except ET.ElementTree.ParseError as e:
                        with open("./error_ipg.xml", mode="w") as efile:
                            downloaded_handle[0].seek(0)
                            efile.write(downloaded_handle[0])
                        
                        raise e
                    else:
                        # Let download manager know about progress
                        DOWNLOAD_MANAGER.download_status(
                            number_left_to_download=len(chunks)-1)
                        
                        # Advance to the next chunk
                        i += 1
                        retries = max_retries
                    finally:
                        downloaded_handle[0] = None
                    
            DOWNLOAD_MANAGER.download_ended()
        
        
        # Figure out which keys did not get returned
        local_keys = [x[0] for x in self._retrieve_ipgft_ids(
            protein_accessions=keys_list)]
        missing_keys = keys.difference(local_keys)
        
        # Return the IPGs for the requested proteins
        requested_ipgs = [x[1] for x in self._retrieve_ipgft_ids(
            protein_accessions=keys_list)]
        ipg_ftdicts_generator = self._retrieve_ipgfts(
            identifiers=requested_ipgs)
        
        return(ipg_ftdicts_generator)
    def _download_ipg_chunk(self, chunk):
        if self.offline:
            assert False, "Called _download_chunk when offline."
        # Download a file into a string.
        file = download_ncbi(filepath=None, id=chunk, 
                             chunksize=len(chunk), verbose=True,
                             db="protein", retmode="xml", 
                             rettype="ipg", into_file=False)
        return(file)
    def import_ipgxml(self, ipg_xml_handle):
        #if isinstance(ipg_xml, str):
        #    ipg_xml = io.StringIO(ipg_xml)
        feature_dicts = [x for x in parse_ipgxml_basic(ipg_xml_handle)]
        self._write_ipgs(feature_dicts=feature_dicts)
    
    # = IPGFeature database handlers =
    @staticmethod
    def _ipgft_entry_into_ftdict(entry):
        ptaccver = entry[4].split(".")
        if len(ptaccver) == 2:
            ptacc,ptver = ptaccver
        else:
            ptacc,ptver = ptaccver,None
        scaccver = entry[8].split(".")
        if len(scaccver) == 2:
            scacc,scver = scaccver
        else:
            scacc,scver = scaccver,None
        
        featdict = {
            "fttype"     : entry[0],
            "ftstart"    : entry[1],
            "ftstop"     : entry[2],
            "ftstrand"   : entry[3],
            "ptacc"      : entry[4],
            "ptver"      : entry[5],
            "ptname"     : entry[6],
            "iptacc"     : entry[7],
            "sciname"    : entry[8],
            "scacc"      : entry[9],
            "scver"      : entry[10],
            "taxid"      : entry[11],
            "taxstrain"  : entry[12],
            "time_added" : entry[13],
        }
        return(featdict)
    def _retrieve_ipgft_ids(self, protein_accessions):
        print("get ipgftids")
        with self.get_cursor() as cur:
            # Retrieve entries in chunks of 5000
            for chunk in chunkify(protein_accessions, 5000):
                results = cur.execute(
                    "SELECT ptacc,iptacc FROM ipgfeats WHERE ptacc in ("\
                      +",".join(["?"]*len(chunk))+")",
                    chunk)
                for result in results:
                    yield(result[0],result[1])
    def _retrieve_ipgfts(self, identifiers):
        print("get ipgfts")
        with self.get_cursor() as cur:
            # Retrieve entries in chunks of 5000 as the database
            # will scream if you try passing it a string several 
            # megabytes in size.  
            for chunk in chunkify(identifiers, 5000):
                ftentries = cur.execute(
                    f"SELECT * FROM ipgfeats WHERE iptacc in ("\
                      +",".join(["?"]*len(chunk))+")",
                    chunk)
                for ftentry in ftentries:
                    yield(self._ipgft_entry_into_ftdict(ftentry))
    def _write_ipgs(self, feature_dicts):
        print("write ipgs")
        with self.get_cursor() as cur:
            for chunk in chunkify(feature_dicts, 500):
                cur.executemany("INSERT INTO ipgfeats VALUES("
                                ":fttype, :ftstart, :ftstop, :ftstrand, "
                                ":ptacc, :ptver, :ptname, :iptacc, :sciname, "
                                f":scacc, :scver, :taxid, :taxstrain, {time.time()})",
                                chunk)
    
    # = = GB/GBSeq Methods = =
    #   Note that gb and gbseq are used as synonyms.
    #   It is preferred to use gbseq, and replace gb.
    #   TODO: Unify nomenclature.
    def obtain_neighborhood_gbs(self, regions, border_size):
        queries = set()
        for region in regions:
            #Request cds info for border_size bp around the cluster
            queries.add((region.ref.sc.accession, 
                         max(region.start - border_size, 1), 
                         region.stop+border_size))
        # Make the request
        return(self.obtain_gbseqs(queries))
    def obtain_gbseqs(self, requests):
        # Requests is a list of tuples describing 
        #   a region in a sequence:
        # 
        #   [("accession", start, stop), ...]
        #
        #   Make sure to use tuples, as
        #   other ducktypes likely won't fly.
        
        # Copy the input so that we don't accidentally modify the
        #   original and cause problems elsewhere.
        requests = list(requests)
        
        # First, get what we can get locally
        
        gbseq_dicts = []
        locally_available = set()
        
        for request,gbseq_dict in self._retrieve_gbs(requests):
            gbseq_dicts.append(gbseq_dict)
            locally_available.add(request)
        
        need_to_get = set(requests).difference(locally_available)
        
        
        # Check with download manager if it's OK to download this much.
        if len(need_to_get) > 0 and not self.offline:
            aborted = DOWNLOAD_MANAGER.download_starting(type="nuccore", 
                      number_to_download=len(need_to_get))
        else:
            aborted = True
        
        if not self.offline and not aborted:
            # * Downloading sequence begins
            
            print("Beginning gb download...")
            
            # Attempt downloading the same sequence at most this
            #   many times before giving up (0 skips everything):
            max_attempts = 2
            attempts = max_attempts
            
            data_to_download = list(need_to_get)
            download_size = len(data_to_download)
            downloaded = []
            failed_to_download = []
            
            while data_to_download and not aborted:
                request = data_to_download[0]
                
                gbseq_xml = self._download_gb_segment(*request)
                
                
                if gbseq_xml is None:
                    # Try again if download fails, until
                    #   the limit is hit.
                    attempts -= 1
                    if attempts == 0:
                        failed_to_download.append(request)
                        del data_to_download[0]
                        attempts = max_attempts
                    continue
                
                
                # Process the gbseq_xml
                gbseq_dict = self.parse_gbseq_gb(io.StringIO(gbseq_xml), 
                                                  request[1],
                                                  request[2])
                self._write_gbseq(gbseq_dict)
                
                # Register the successful download
                downloaded.append(request)
                del data_to_download[0]
                
                # Perform progress update
                aborted = DOWNLOAD_MANAGER.download_status(
                    number_left_to_download=len(data_to_download))
                print(f"\rDownloaded {len(downloaded)}/{download_size}, "
                      f"{len(failed_to_download)} failed.", end="")
            
            DOWNLOAD_MANAGER.download_ended()
            print("Download complete.")
            
            # Add the downloaded sequences to what was retrieved before.
            # Maybe we could not pull the downloaded ones into memory
            #       all at once and use a generator instead, but honestly
            #       would it make a difference at this point?
            for request,gbseq_dict in self._retrieve_gbs(downloaded):
                gbseq_dicts.append(gbseq_dict)
                locally_available.add(request)
            
        return(gbseq_dicts)
    @staticmethod
    def parse_gbseq_gb(handle, gbseq_start, gbseq_stop):
        # We use BioPython's gb parser but convert the results into
        #   cluseek's native classes
        
        seqrec = SeqIO.read(handle, "gb")
        bioproject = ""
        biosample = ""
        assembly = ""
        for dbxref in seqrec.dbxrefs:
            if "bioproject" in dbxref.lower():
                bioproject = dbxref.split(":")[1]
            elif "biosample" in dbxref.lower():
                biosample = dbxref.split(":")[1]
            elif "assembly" in dbxref.lower():
                assembly = dbxref.split(":")[1]
        
        gbfeat_dicts = []
        stranddict = {None: "0",
                      1: "+",
                      -1: "-"}
        for seqfeat in seqrec.features:
            gbfeat_dict = {
                "fttype": seqfeat.type.lower(),
                "ftstart": int(seqfeat.location.start) + gbseq_start,
                "ftstop": int(seqfeat.location.end) + gbseq_start - 1,
                "ftstrand": stranddict[seqfeat.strand],
                "ptacc": None,
                "ptver": None,
                "ptname": None,
                "pttype": None,
                "ptseq": None,
            }
            if gbfeat_dict["fttype"] == "cds" and "protein_id" in seqfeat.qualifiers:
                gbfeat_dict["ptacc"]  = seqfeat.qualifiers["protein_id"][0].split(".")[0]
                gbfeat_dict["ptver"]  = seqfeat.qualifiers["protein_id"][0].split(".")[1]
                gbfeat_dict["ptname"] = ""
                gbfeat_dict["pttype"] = ", ".join(seqfeat.qualifiers["product"])\
                                        if "product" in seqfeat.qualifiers else\
                                        ""
                gbfeat_dict["ptseq"]  = seqfeat.qualifiers["translation"][0]
                
                if len(seqfeat.qualifiers["protein_id"]) > 1:
                    print("WARNING: Multiple accessions per protein found, "
                          "discarding all but the first.")
                if len(seqfeat.qualifiers["translation"]) > 1:
                    print("WARNING: Multiple sequences per protein found, "
                          "discarding all but the first.")
            
            gbfeat_dicts.append(gbfeat_dict)
        
        gbseq_dict = {
            "regstart": gbseq_start,
            "regstop": gbseq_stop,
            "regseq": str(seqrec.seq),
            "scacc": seqrec.id.split(".")[0],
            "scver": seqrec.id.split(".")[1],
            "taxsciname": seqrec.annotations.get("organism"),
            "taxonomy": list(seqrec.annotations.get("taxonomy")),
            "biosample": biosample,
            "bioproject": bioproject,
            "features": gbfeat_dicts,
            "topology": seqrec.annotations.get("topology"),
            "references": str(seqrec.annotations.get("references")),
            "comment": str(seqrec.annotations.get("comment"))
        }
        return(gbseq_dict)
    @staticmethod
    def parse_gbseq_xml(handle, gbseq_start, gbseq_stop):
        offset = gbseq_start
        #Reads a genbank XML file. DOES NOT COLLECT ALL INFORMATION!!!
        #  This parser could originally read through multiple records inside a single XML,
        #  but this has been changed due to problems with keeping track of the offset.
        #This parser *needs* to know the offset of the genbank file relative to the contig, as
        #  without it, the neighbourhood will be misaligned relative to the reference, and
        #  may end up overlapping with other neighbourhoods in the same contig.
        #  By as of writing, the offset (or rather the start/stop positions of the neighbourhood)
        #  are listed both in genbank(.gb) filenames and in the _index.txt
        def parse_position(raw, position_offset):
            #Handles (some) of the shapes position data can manage
            #Likely can't handle anything with introns or otherwise eukaryotic
            #TODO:
            #The current implementation is painfully hacky, but it stays until I can figure out
            #  how to make python process functional statements in strings without using eval
            raw=raw.replace(">","")
            raw=raw.replace("<","")
            if "complement" in raw:
                strand="-"
                raw = raw.lstrip("complement(").rstrip(")")
            else:
                strand="+"
            if "join" in raw:
                raw = raw.lstrip("join(").rstrip(")").split(",")
                raw = "..".join([raw[0].split("..")[0], raw[1].split("..")[1]])
            raw=raw.split("..")
            try:
                #TODO: A bizzare behaviour from the xml.etree parser occurs where
                #      an element.tag gets read as <1 instead of whatever it should be.
                #      I have no idea why this happens or how to stop it--
                #      So for now, I just handle the exceptions.
                #NOTE: Isn't this literally just "this feature begins before the
                #      start of the sequence"?
                #      Though I do seem to recall xml.etree actually misreading the
                #      entries. Either way, strange.
                
                #NOTE: The -1 below is compensating for offset calculations being 
                #      one bp off because sequence positions start counting from 1
                #      and that 1 gets doubled when you add two positions together.
                start = int(raw[0]) + position_offset - 1
                stop  = int(raw[1]) + position_offset - 1     
                return(start,stop,strand)
            except:
                return None
        
        
        feature = None
        record = None
        
        # Recorded qualifier tags:
        recquals = set(["product", "protein_id", "translation"])
        gbqual = None
        # Recorded xrefs
        recxrefs = {"BioProject", "BioSample"}
        xref = None
        for event, elem in ET.iterparse(handle, events=("start","end")):
            # Handling feature qualifiers
            if event=="start" and elem.tag=="GBQualifier":
                gbqual = {"name": None, "value": None}
            elif event=="end" and elem.tag=="GBQualifier_value":
                gbqual["value"] = elem.text
            elif event=="end" and elem.tag=="GBQualifier_name":
                gbqual["name"] = elem.text
            elif event=="end" and elem.tag=="GBQualifier":
                if gbqual["name"] in recquals and gbqual["value"] is not None:
                    feature[gbqual["name"]] = gbqual["value"]
            # Handling features
            elif event=="end" and elem.tag=="GBFeature_location":
                res = parse_position(elem.text, offset)
                if res is None:
                    res = (-1, -1, None)
                    print("Encountered unknown error while parsing sequence {}.".format(record["accession"]))
                    skip_feature = True
                feature["start"],feature["stop"],feature["strand"] = res
            elif event=="end" and elem.tag=="GBFeature_key":
                feature["type"] = elem.text.lower()
            elif event=="start" and elem.tag=="GBFeature":
                # Integrate previous feature
                if feature:
                    if feature["type"] != "source" and not skip_feature:
                        record["features"].append(feature)
                # Create new feature
                skip_feature = False
                feature = {
                    "type": None,
                    "start": None,
                    "stop": None,
                    "strand": None,
                    # Also includes any recquals declared above.
                    #   These may not always be present (eg for nonproteins)
                    "product": None,
                    "protein_id": None,
                    "translation": None,
                    "scacc": record["accession"],
                }
            elif event=="start" and elem.tag=="GBSeq_feature-table":
                record["features"] = []
            elif event=="end" and elem.tag=="GBSeq_organism":
                record["sciname"] = elem.text
            elif event=="end" and elem.tag=="GBSeq_primary-accession":
                record["accession"] = elem.text
            elif event=="end" and elem.tag=="GBSeq_taxonomy":
                record["taxonomy"] = elem.text
            # Parsing gbx references
            elif event=="start" and elem.tag=="GBXref":
                xref = {"dbname": None, "dbid": None}
            elif event=="end" and elem.tag=="GBXref_dbname":
                xref["dbname"] = elem.text
            elif event=="end" and elem.tag=="GBXref_id":
                xref["dbid"] = elem.text
            elif event=="end" and elem.tag=="GBXref":
                if xref["dbname"] in recxrefs and xref["dbid"] is not None:
                    record[xref["dbname"].lower()] = xref["dbid"]
            # new record
            elif event=="start" and elem.tag=="GBSeq":
                record = {
                    "accession": None,
                    "start": gbseq_start,
                    "stop": gbseq_stop,
                    "taxid": None, # This never gets filled in.
                    "sciname": None,
                    "taxonomy": None, # It's a list of taxonomic groups
                    "bioproject": None, # may not always be applicable
                    "biosample": None, # may not always be applicable
                    "features": None,
                }
        return(record)
    def _download_gb_segment(self, accession, start, stop):
        assert start>=1, f"Start position must be 1 or greater! Instead, it is {start}."
        
        chunks = []
        try:
            handle = Entrez.efetch(
                id=accession, db="nuccore", rettype="gb", 
                retmode="text", seq_start=start, 
                seq_stop=stop)
            for line in handle:
                if isinstance(line, bytes):
                    line = line.decode("utf-8")
                chunks.append(line)
        except Exception as e:
            print("Fetch failed!")
            return(None)
        return("".join(chunks))
    
    # = GB database handlers =
    def _write_gbseq(self, gbseq_dict):
        #TODO: Add a mechanism for removing redundant
        #      gbseq entries.
        #      EG: if a larger gbseq completely covers
        #          the region of a smaller gbseq
        print("write gbseq")
        with self.get_cursor() as cur:
            values = {"accession": gbseq_dict["scacc"],
                      "start": gbseq_dict["regstart"],
                      "stop": gbseq_dict["regstop"],
                      "data": wrap_data(gbseq_dict),
                      "time_added": time.time(),
                    }
            
            # Save gbseqs
            cur.execute("INSERT INTO gbseqs VALUES("
                        ":accession, :start, :stop, :data, "
                        ":time_added)",
                        values)
    def _retrieve_gbs(self, requests):
        # Requests is a list of tuples describing a region in a sequence
        #   [(accession, start, stop), ...]
        print("retrieve gbs")
        with self.get_cursor() as cur:
            failed = 0
            # Going one by one is significantly slower than making a single
            #   large request, but probably irrelevant to optimize.
            for request in requests:
                
                sql = ("SELECT * FROM gbseqs "
                       "WHERE accession = ? " 
                       "AND start <= ? "
                       "AND stop >= ?")
                try:
                    raw_results = cur.execute(sql, request).fetchall()
                except Exception as e:
                    print(request)
                    raise e
                
                # 1: Acc, 2: Start, 3: Stop, 4: Data, 5: Time Added
                gbseq_dicts = [unwrap_data(raw_result[3]) for raw_result in raw_results]
                
                # We always want to serve one result per
                #   one request, even if we have multiple
                #   overlapping entries that fit the criteria.
                if len(gbseq_dicts) == 0:
                    failed += 1
                    continue
                elif len(gbseq_dicts) == 1:
                    gbseq_dict = gbseq_dicts[0]
                else:
                    #   If multiple are available, then
                    #   we want to use the entry with the
                    #   biggest margin from either side.
                    gbseq_dict = max(gbseq_dicts, 
                                      key=lambda e: min(request[1]-e["regstart"],
                                                           e["regstop"]-request[2]))
                
                # Trim the gbseq_dict to the request length.
                left_trim = request[1] - gbseq_dict["regstart"]
                right_trim = request[2] - gbseq_dict["regstart"]+1
                trimmed_seq = gbseq_dict["regseq"][left_trim:right_trim]
                
                gbseq_dict["regstart"] = request[1]
                gbseq_dict["regstop"]  = request[2]
                gbseq_dict["regseq"] = trimmed_seq
                
                # And done.
                # We yield both the original request and result
                #   so we can find which requests failed later.
                yield(request, gbseq_dict)
            print(f"{failed} gbseqs were not found in local database")
    
    # = = Inputs = =
    def save_blastpxml_file_into_db(self, path):
        # TODO: Include checks if this is a valid BLAST XML file?
        handle = open(path, mode="r")
        self._write_blastpxml(handle)
        print(f"Saved XML into db: {path}")
    
    def save_coloc_config(self, config):
        # We save colocalization config into metadata to avoid breaking backwards
        #   compatibility.
        config = wrap_data(config)
        with self.get_cursor() as cursor:
            cursor.execute(
                "DELETE from cluseek_metadata WHERE key=?", ("coloc_config",))
            cursor.execute(
                "INSERT INTO cluseek_metadata VALUES(:key, :value)",
                ("coloc_config", config))
    def get_coloc_config(self):
        with self.get_cursor() as cursor:
            config_raw = cursor.execute(
                "SELECT key, value FROM cluseek_metadata WHERE key = ?",
                ("coloc_config",)).fetchall()
            print(config_raw)
            config = dict()
            for key,value in config_raw:
                print("Found colocalization config under key", key)
                config = unwrap_data(value)
        return(config)
    # = Input database handlers =
    def _write_blastpxml(self, handle):
        print("get blastpxml")
        text = handle.read().replace("CREATE_VIEW\n","")
        with self.get_cursor() as cur:
            compressed_xml = zlib.compress(text.encode("utf-8"), level=9)
            
            cur.execute("INSERT INTO blastpxml VALUES( ? )", (compressed_xml,))
    def _retrieve_all_blastpxml(self):
        print("get all blastpxml")
        with self.get_cursor() as cur:
            inputs = cur.execute("SELECT * FROM blastpxml")
            
            for input in inputs:
                yield(io.StringIO(zlib.decompress(input[0]).decode("utf-8")))
        
    # = Remote BLAST =
    def remote_blast_inputs(self, queries, blast_config):
        big_query = "\n".join(queries)
        
        #1/0
        #fastas=big_query.
        
        
        self._write_blastpxml(self._remote_blast(big_query, **blast_config))
            
    @staticmethod
    def _remote_blast(query, db="nr", expect=10.0, filter=None, 
                     entrez_query=None, nhits=20000,
                     gapcosts="11 1", 
                     matrix_name="BLOSUM62", 
                     threshold=11, 
                     word_size=6, 
                     comp_based_statistics=2):
        if isinstance(query, list):
            query = "\n".join(query)
        blast = NCBIWWW.qblast("blastp", database=db, sequence=query, expect=expect, 
                        descriptions=nhits, alignments=nhits, filter=filter, 
                        format_type="XML", entrez_query=entrez_query, hitlist_size=nhits,
                        gapcosts=gapcosts, matrix_name=matrix_name, threshold=threshold, 
                        word_size=word_size, composition_based_statistics=comp_based_statistics)
        return(blast)
    
    # = = Neighborhood View = =
    def purge_neidata(self, nei_id):
        print("purge neiviews")
        with self.get_cursor() as cur:
            cur.execute("DELETE FROM neiviews WHERE nei_id=?", (nei_id,))
            cur.execute("DELETE FROM neiview_clusters WHERE nei_id=?", (nei_id,))
    def write_neidata(self, neiview):
        nei_id = neiview.id_
        
        # * * Prepare Neighborhood info
        # Regions
        regdicts = []
        for index in range(len(neiview.regions_all)):
            regui = neiview.regions_all[index]
            regdict = {
                "accession":regui.reg.sc.accession,
                "start":regui.reg.start,
                "stop":regui.reg.stop,
                "index":index,
                "reversed":regui.reversed,
                "selected":regui.selected,
                "offset":regui.offset,
                # Additional data
                "tags": [tag.data["id"] for tag in regui.tags],
                "last_align": regui.last_align.id_ if regui.last_align else None,
                "displayed": regui.displayed,
                "hidden": regui.hidden,
            }
            regdicts.append(regdict)
        
        # Configuration
        config = dict(neiview.display_policy)
        
        # Finalize input
        nei_dict = {
            "nei_id": nei_id,
            "regions": wrap_data(regdicts),
            "config": wrap_data(config),
        }
        
        
        # * * Prepare clusters
        clu_dicts = []
        for cluster in neiview.neidata.cluster_hierarchy.clusters_all.values():
            clu_dict = {
                "nei_id": nei_id,
                "cluster_id": cluster.id_,
                "type_": cluster.type_,
                "centroid": cluster.centroid.accession if cluster.centroid else None,
                "parent": cluster._parent.id_ if cluster._parent else None,
                "proteins": ";".join(protein.accession \
                                    for protein in cluster.proteins.values()) \
                                    if not cluster.subclusters \
                                    else None,
                "metadata": wrap_data(cluster._metadata),
                "styledict": wrap_data(cluster.styledict_config),
            }
            clu_dicts.append(clu_dict)
        print("\tWrote neiviews")
        
        
        # Purge old save
        saved_ids = self.get_available_neiviews()
        if neiview.id_ in saved_ids:
            self.purge_neidata(neiview.id_)
        
        print("write neidata")
        with self.get_cursor() as cur:
            # Perform db operation
            
            # * Write neighborhood info to database
            cur.execute("INSERT INTO neiviews VALUES("
                            ":nei_id, :regions, :config)",
                        nei_dict)
            # * Write cluster info to database
            # May need to adjust the size of chunks so we don't overwhelm the
            #   input. These entries could get quite long.
            for chunk in chunkify(clu_dicts, 500):
                cur.executemany("INSERT INTO neiview_clusters VALUES("
                                    ":nei_id, :cluster_id, :type_, :centroid, "
                                    ":parent, :proteins, :metadata, :styledict)",
                                chunk)
            print("\tWrote clusters")
    def get_available_neiviews(self):
        print("get avail neiviews")
        with self.get_cursor() as cur:
            rows = cur.execute("SELECT nei_id FROM neiviews")
            return([row[0] for row in rows])
    def get_neiview(self, nei_id, dataset):
        print("get neviews")
        with self.get_cursor() as cur:
            neiview_data = cur.execute("SELECT regions,config FROM neiviews WHERE nei_id=?", (nei_id,))
            regdicts,cfg = neiview_data.fetchone()
        # Region data tuple is comprised of:
        #   accession, start, stop, index, reversed, selected, offset
        regdicts = unwrap_data(regdicts)
        regdicts.sort(key=lambda x: x["index"]) # Sort by index
        
        config = unwrap_data(cfg)
        
        if "creation_settings" in config:
            config["creation_settings"]["loading_existing_session"] = True
            settings = dict(config["creation_settings"])
        else:
            settings = {"loading_existing_session": True, "creation_data_missing": True}
        neidata = uiqt.NeiData([], dataset, settings)
        
        region_data_dict = {}
        for regdict in regdicts:
            reg = uiqt.dframe.GeneticRegion(
                dataset,dataset.root.scAll[regdict["accession"]],
                regdict["start"],regdict["stop"])
            region_data_dict[reg] = regdict
        neidata.regions_to_display = list(region_data_dict.keys())
        
        neidata.p1_download_neighborhoods()
        
        sql = ("SELECT cluster_id, type_, centroid, parent, proteins, "
                      "metadata, styledict "
                    "FROM neiview_clusters "
                    "WHERE nei_id = ?")
        
        with self.get_cursor() as cur:
            neiclusters = cur.execute(sql, (nei_id,))
            hierarchy = uiqt.dframe.ProteinClusterHierarchy(dataset.root)
            if "cluster_graph" in config:
                hierarchy.set_graph(config["cluster_graph"])
            else:
                hierarchy.set_graph(nx.Graph())
            
            # Defer subcluster assignment until all clusters have been created,
            #   storing pairs in lineage_pairs
            lineage_pairs = []
            for cluster_id,type_,centroid_id,parent_id,\
              protein_ids,metadata,styledict in neiclusters:
                cluster = hierarchy.get_or_create(cluster_id, type_=type_)
                
                cluster._metadata.update(unwrap_data(metadata))
                if cluster._metadata["local_group"] is not None:
                    assert isinstance(cluster._metadata["local_group"], int)
                    cluster.set_local_group(cluster._metadata["local_group"])
                
                # Incorporate new categories into 
                cluster.styledict_config = unwrap_data(styledict)
                cluster.styledict_config.update()
                
                if parent_id:
                    lineage_pairs.append((cluster_id, parent_id))
                
                protein_ids = protein_ids.split(";") if protein_ids else []
                for protein_id in protein_ids:
                    hierarchy.add_protein(dataset.root.ptAll[protein_id], 
                                          cluster_id)
                if centroid_id:
                    cluster.centroid = dataset.root.ptAll[centroid_id]
        
        for child_id,parent_id in lineage_pairs:
            parent = hierarchy.clusters_all[parent_id]
            child = hierarchy.clusters_all[child_id]
            parent.add_subcluster(child)
        
        # Recompute styledicts after styledicts and hierarchy has been assigned
        #   We only need to prompt toplevel clusters (hierarchy.clusters), and
        #   changes should propagate down the hierarchy in the correct sequence.
        for cluster in hierarchy.clusters.values():
            cluster.update_styledict()
        
        neidata.cluster_hierarchy = hierarchy
        
        # Prepare neiview object
        neiview = uiqt.NeiView(neidata, nei_id)
        # Using update instead of substitution allows for new categories to be
        #   added to old save files.
        #   Load display policy BEFORE initializing displayed data pls.
        neiview.display_policy.update(config)
        neiview.init_displayed_data(jaccard=False)
        # This is not redundant, it forces the setter to activate
        #   and initialize values
        neiview.displayname = neiview.displayname
        
        for regui in neiview.regions_all:
            regdict = region_data_dict[regui.reg]
            
            regui.set_reversed(regdict["reversed"])
            regui.set_selected(regdict["selected"])
            regui.set_offset(regdict["offset"])
            #
            regui.set_hidden(regdict["hidden"] if "hidden" in regdict else False)
            regui.set_displayed(regdict["displayed"] if "displayed" in regdict else True)
            
            last_align = regdict.get("last_align")
            if last_align:
                last_align = hierarchy.clusters_all[last_align]
            else:
                last_align = None
            regui.last_align = last_align
            
            if "tags" not in regdict or regdict["tags"] is None:
                regdict["tags"] = []
            for tag_id in regdict["tags"]:
                regui.add_tag(neiview.display_policy["all_tags"][tag_id])
        
        sorted_regs = sorted(
                neiview.regions_all,
                key=lambda regui: region_data_dict[regui.reg]["index"])
        neiview.sort_by_list(sorted_regs)
        
        # I think somewhere in here is the error. Make sure the variables
        #   here are properly insulated from everything else
        #   to prevent loading errors
        def load_rules():
            # Load rules
            untranslated = list(neiview.display_policy["restriction_rules"])
            neiview.display_policy["restriction_rules"] = []
            for value in untranslated:
                print(type(value), value)
                assert isinstance(value, list)
                if value[0] == "!class:SelectionManager.Rule_All":
                    value = uiqt.SelectionManager.Rule_All._from_dict(value[1], neiview)
                elif value[0] == "!class:SelectionManager.Rule_None":
                    value = uiqt.SelectionManager.Rule_None._from_dict(value[1], neiview)
                elif value[0] == "!class:SelectionManager.Rule_AtLeast":
                    value = uiqt.SelectionManager.Rule_AtLeast._from_dict(value[1], neiview)
                elif value[0] == "!class:SelectionManager.Rule_AtMost":
                    value = uiqt.SelectionManager.Rule_AtMost._from_dict(value[1], neiview)
                else:
                    raise ValueError("Invalid rule string found while loading neiview: "+value)
                neiview.selection_manager.add_rulewidget(value)
        neiview.sig_selection_manager_created.connect(load_rules)
        
        #neiview.sort_by_list([])
        return(neidata, neiview)
    def get_new_neiview_id(self):
        return(max(self.get_available_neiviews()+[-1])+1)
    
    
class ManagerClus():
    def __init__(self):
        pass
    def get_diamond_path(self):
        if sys.platform in ("win32"):
            if getattr(sys, "frozen", False):
                # Windows Frozen
                path = os.path.join(
                    sys._MEIPASS, "diamond-win64.exe")
            else:
                # Windows fluid
                path = os.path.join(
                    os.path.dirname(__file__), 
                    "diamond", "diamond-win64.exe")
        elif sys.platform in ("linux"):
            
            if getattr(sys, "frozen", False):
                # We don't create frozen releases on linux so this is untested.
                # Linux frozen
                path = os.path.join(
                    sys._MEIPASS, "diamond-linux64-2")
            else:
                # Linux fluid
                path = os.path.join(
                    os.path.dirname(__file__), "diamond", "diamond-linux64-2")
        elif sys.platform in ("darwin"):
            if getattr(sys, "frozen", False):
                # OSX Frozen
                path = os.path.join(
                    sys._MEIPASS, "diamond-osx-arm64")
            else:
                # OSX Fluid
                path = os.path.join(
                    os.path.dirname(__file__), "diamond", "diamond-osx-arm64")
        else:
            raise Exception("Unable to determine operating system.")
        return(path)
    # = General =
    def _write_protein_fastas(self, path, accessions, root, verbose=True, key=lambda x: len(x.seq)):
        t0 = time.time()
        errors = Counter()
        
        #Get all the proteins
        pts = []
        for accession in accessions:
            pt = root.ptAll[accession]
            if pt.seq is None:
                errors["No sequence in protein"] += 1
                continue
            errors["Completed"] += 1
            pts.append(pt)
        
        #Sort sequences from shortest to longest
        pts.sort(key=key)
        
        # Write all sequences
        #   the with statement should close any open files
        #   if this isn't the case, replace it with a conventional
        #   try..except..finally clause
        with open(path, mode="w") as fastadump:
            for pt in pts:
                fastadump.write(f">{pt.accession}\n{pt.seq}\n")
        if verbose:
            print(errors)
        print(f"Completed fasta dump in {time.time()-t0} seconds.")
    
    # = Global Clustering = 
    def run_global_clustering(self, accessions, root, identity, coverage=80):
        # Create temporary directory
        temp_dir = tempfile.TemporaryDirectory()
        
        path_input = os.path.join(temp_dir.name, "input.fsa")
        path_db = os.path.join(temp_dir.name, "db.dmnd")
        path_output = os.path.join(temp_dir.name, "output")
        
        try:
            # * Write the FASTA
            self._write_protein_fastas(path_input, accessions, root)
            
            # * Convert FASTA into diamond database
            arguments = [
                self.get_diamond_path(),
                "makedb",
                "--threads", "2",
                "--tmpdir", temp_dir.name,
                "--in", path_input,
                "--db", path_db,
                "--quiet",
            ]
            
            subprocess.call(arguments)
               
            # * Run DIAMOND
            # Clustering
            arguments = [
                self.get_diamond_path(), 
                "cluster",
                "--tmpdir", temp_dir.name,
                "--memory-limit", "16G", #16G
                "--approx-id", str(identity), #default%: 50
                #"--member-cover", str(coverage), #default%: 80
                "--mutual-cover", str(coverage),
                "--db", path_db,
                "--out", path_output,
                "--quiet"
            ]
            subprocess.call(arguments)
            
            # * Parse the output
            parsed = self._parse_global_clustering(path_output, root)
            return(parsed)
        except Exception as e:
            raise e
        finally:
            temp_dir.cleanup()
    @staticmethod
    def _parse_global_clustering(path, root):
        repr_map = {}
        hierarchy = dframe.ProteinClusterHierarchy(root)
        with open(path, mode="r", encoding="utf-8") as results_handle:
            for line in results_handle:
                line = line.rstrip("\n")
                repr_id,member_id = line.split("\t")
                repr,member = root.ptAll[repr_id], root.ptAll[member_id]
                
                if repr not in repr_map:
                    repr_map[repr] = hierarchy.new_cluster(
                        type_="globally_aligned")
                    hierarchy.add_protein(
                        repr,
                        repr_map[repr].id_,
                        is_centroid=True)
                
                hierarchy.add_protein(
                    member,
                    repr_map[repr].id_,
                    is_centroid=False)
        return(hierarchy)
    
    # = Local Clustering = 
    def run_local_clustering_of_global_clusters(self, clustering_result, 
                                                evalue, identity, bitscore,
                                                sensitivity,
                                                community_weight_variable,
                                                community_resolution):
        def extract_centroids_from_clusters(subset_type):
            #inclusters are globally aligned clusters
            #make a list of clusters sorted by length of centroid
            inclusters = set([clus for clus in clustering_result.clusters.values()])
            
            #Check and debug for missing clusters
            error_missing_centroids = 0
            get_rid = set()
            for clus in inclusters:
                if not clus.type_ == subset_type:
                    get_rid.add(clus)
                if not clus.centroid:
                    get_rid.add(clus)
                    error_missing_centroids += 1
            inclusters = list(inclusters - get_rid)
            if error_missing_centroids:
                print(f"DEBUG: {error_missing_centroids} had a None representative.")
            
            queries = []
            for clus in sorted(inclusters, 
                key=lambda x: len(x.centroid.seq),
                reverse=True):
                queries.append((clus.id_, clus.centroid.seq))
            
            return(queries)
        
        queries = extract_centroids_from_clusters(subset_type="globally_aligned")
        
        alignments = list(self.multiquery_blastp(
            query_seqs=queries,
            db_seqs=queries,
            chunk_size=50000,
            evalue=evalue,
            identity=identity,
            bitscore=bitscore,
            sensitivity=sensitivity,
        ))
        
        # we sort alignments by descending bitscore
        alignments.sort(key=lambda x: x["bitscore"],
                        reverse=True)
        
        
        # Prepare a graph
        graph = nx.Graph()
        clustering_result.set_graph(graph)
        
        for query_id,query_seq in queries:
            graph.add_node(query_id, sequence=query_seq)
        
        for alignment in alignments:
            # This only allows at most one edge between two nodes (does it?)
            #   I don't really care because all we need is one to establish
            #   single linkage.
            alignment_copy = dict(alignment)
            del alignment_copy["query"]
            del alignment_copy["hit"]
            graph.add_edge(
                alignment["query"], 
                alignment["hit"],
                **alignment_copy)
        
        # Separate into disjunct subgraphs and detect communities
        clusters = []
        for cluster in nx.k_edge_components(graph, 1):
            cluster_subgroups = []
            
            if len(cluster) < 2:
                cluster_subgroups.append(list(cluster))
            else:
                for community in nx.community.greedy_modularity_communities(
                  graph.subgraph(cluster),
                  weight=community_weight_variable,
                  #resolution=(0.2*community_resolution+0.8*community_resolution*len(cluster)/1000)):
                  resolution=community_resolution):
                    cluster_subgroups.append(list(community))
                
                clusters.append(cluster_subgroups)
        
        # Convert into dframe cluster structure
        assigned = set()
        local_group_id = 0
        for cluster_subgroups in clusters:
            #supercluster = clustering_result.new_cluster(
            #    "locally_aligned",
            #    hidden=True)
            
            for subgroup in cluster_subgroups:
                subgroup_cluster = clustering_result.new_cluster(
                                    type_="community_based")
                #subgroup_cluster.set_local_group(local_group_id)
                
                for cluster_id in subgroup:
                    assert cluster_id not in assigned
                    assert isinstance(cluster_id, str)
                    assigned.add(cluster_id)
                    subgroup_subcluster = clustering_result.clusters[cluster_id]
                    
                    # For now, we only add local group ID to bottomlevel clusters
                    subgroup_subcluster.set_local_group(local_group_id)
                    
                    subgroup_cluster.add_subcluster(subgroup_subcluster)
                
                #supercluster.add_subcluster(subgroup_cluster)
            
            local_group_id += 1
        
        return(clustering_result)
        
        
    @staticmethod
    def cluster_local_alignments(alignments, weight_variable="bitscore"):
        # Make sure we're working with a list, not a generator.
        alignments = list(alignments)
        
        # Put together graph
        graph = nx.Graph()
        
        for alignment in alignments:
            if alignment["query"] == alignment["hit"]:
                continue
            
            graph.add_edge(
                alignment["query"],
                alignment["hit"],
                weight = alignment[weight_variable],
                alignment = alignment)
        
        # Identify fully disjunct areas 
        disjunct_groups = nx.k_edge_components(graph, 1)
        
        # Identify communities
        community_groups = nx.community.louvain_communities(graph)
    
    
    def multiquery_blastp(self, query_seqs, db_seqs, 
        evalue, identity, bitscore, sensitivity="--sensitive",
        chunk_size=50000):
        # query_seqs and db_seqs are FASTA sequences in the format
        # [(id, AA sequence), (id, AA sequence), ...]
        
        # Copy the lists, just in case.
        #   We WILL be modifying them and I'd rather not cause problems
        #   upstream.
        query_seqs = list(query_seqs)
        db_seqs = list(db_seqs)
        
        # Create temporary directory
        temp_dir = tempfile.TemporaryDirectory()
        try:
            # These temporary paths within the directory will be used
            path_rawdb = os.path.join(temp_dir.name, "rawdb.fsa")
            path_db = os.path.join(temp_dir.name, "db.dmnd")
            path_query = os.path.join(temp_dir.name, "query.fsa")
            path_output = os.path.join(temp_dir.name, "output")
            
            def run_blastp(query):
                # Create query FASTA
                with open(path_query, mode="w") as queryfile:
                    i=0
                    for header,sequence in query:
                        queryfile.write(f">{header}\n{sequence}\n")
                        #if isinstance(x, str):
                        #    # If it's a string, just give it an arbitrary ID
                        #    queryfile.write(f">unnamed_sequence_{i}\n{x}\n")
                        #    i+=1
                        #elif isinstance(x, dframe.ProteinCluster):
                        #    # If it's a cluster, use the cluster's id_ and the centroid
                        #    queryfile.write(f">{x.id_}\n{x.centroid.seq}\n")
                        #elif isinstance(x, dbdl.Protein):
                        #    # If it's not either of those, it's PROBABLY a dbdl.Protein
                        #    queryfile.write(f">{x.accession}\n{x.seq}\n")
                        #else:
                        #    # And if it's not that either, cry about it.
                        #    raise ValueError(f"Invalid query: {str(query)}")
                    queryfile.flush()
                    queryfile.close()
                
                arguments = [
                    self.get_diamond_path(),
                    "blastp",
                    "--threads", "2",
                    "--db", path_db,
                    sensitivity,
                    "--query", path_query,
                    "--out", path_output,
                    "--tmpdir", temp_dir.name,
                    "--quiet",
                    "-k", "0",
                ]
                
                if bitscore is not None:
                    arguments.extend(["--min-score", str(bitscore)])
                if evalue is not None:
                    arguments.extend(["--evalue", str(evalue)])
                if identity is not None:
                    # Diamond accepts identity as an integer from 0 to 100
                    arguments.extend(["--id", str(identity)])
                print(arguments)
                # Can also use --query-cover, --subject-cover...
                
                print(str(bitscore), str(evalue), str(identity))
                
                
                # Call diamond itself
                subprocess.call(arguments)
                
                # Then we parse those results.
                results = self._parse_blast6out_results(path_output)
                
                return(results)
            
            # Export the sequences for a database
            with open(path_rawdb, mode="w") as fastadump:
                for header,sequence in db_seqs:
                    fastadump.write(f">{header}\n{sequence}\n")
            
            # Convert to diamond db
            arguments = [
                self.get_diamond_path(),
                "makedb",
                "--threads", "2",
                "--tmpdir", temp_dir.name,
                "--in", path_rawdb,
                "--db", path_db
            ]
            subprocess.call(arguments)
            

            #Loop over queries in chunks
            finished = False
            while len(query_seqs) != 0:
                # * Take {chunk_size} queries
                chunk = query_seqs[0:min(chunk_size, len(query_seqs))]
                
                #Remove these queries
                query_seqs = query_seqs[min(chunk_size, len(query_seqs)):]
                
                # * Align it with the database
                alignments = run_blastp(chunk)
                
                for alignment in alignments:
                    yield(alignment)
        except Exception as e:
            raise e
        finally:
            temp_dir.cleanup()
    
    @staticmethod
    def _parse_blast6out_results(resultfile):
        #Column description:
        # (0)label, (1)target, (2)%identity, (3)align_length, (4)n_mismatches,
        # (5)n_gap_opens, (6)startpos_in_query, (7)endpos_in_query,
        # (8)startpos_in_hit, (9)endpos_in_hit,
        # (10)evalue, (11)bitscore
        # S,S,F,I,I,I,I,I,I,I,F,F
        results = []
        with open(resultfile) as ffile:
            rfile = [None if line=="" else (line.split("\t")) for line in ffile.read().split("\n")]
            ffile.close()
        for line in rfile:
            if line is None:
                continue
            results.append({
                "query": line[0], 
                "hit": line[1], 
                "pidentity": float(line[2]), 
                "align_length": int(line[3]), 
                "n_mismatches": int(line[4]), 
                "n_gap_opens": int(line[5]), 
                "startpos_in_query": int(line[6]), 
                "endpos_in_query": int(line[7]), 
                "startpos_in_hit": int(line[8]), 
                "endpos_in_hit": int(line[9]), 
                "evalue": float(line[10]), 
                "bitscore": float(line[11])})
        return(results)


def stringify_data(data):
    # Iterates over data, stringifying it so it can be converted
    #   into JSON
    # Supports dict and list, tuple and set will be turned into list. 
    # Supports whatever types uiqt.stringify supports
    if isinstance(data, dict):
        new = dict()
        for key,value in zip(data.keys(),data.values()):
            key = uiqt.stringify(key)
            if isinstance(value, (dict,list,set,tuple)):
                value = stringify_data(value)
            else:
                value = uiqt.stringify(value)
            new[key] = value
        return(new)
    elif isinstance(data, (list,tuple,set)):
        new = list()
        for value in data:
            if isinstance(value, (dict,list,set,tuple)):
                new.append(stringify_data(value))
            else:
                new.append(uiqt.stringify(value))
        if isinstance(data,tuple):
            new=tuple(new)
        elif isinstance(data,set):
            new=set(new)
        return(new)
    else:
        raise ValueError(str(type(data))+str(data))
def unstringify_data(data):
    # Reverses stringify_data
    if isinstance(data, list)\
      and len(data) == 2\
      and isinstance(data[0], str)\
      and data[0].startswith("!class:"):
        # If this tuple is actually a class instance container
        new = uiqt.unstringify(data)
        return(new)
    
    if isinstance(data, dict):
        new = dict()
        for key,value in zip(data.keys(),data.values()):
            key = uiqt.unstringify(key)
            if isinstance(value, (dict,list,set,tuple)):
                value = unstringify_data(value)
            else:
                value = uiqt.unstringify(value)
            new[key] = value
        return(new)
    elif isinstance(data, (list,tuple,set)):
        new = list()
        for value in data:
            if isinstance(value, (dict,list,set,tuple)):
                new.append(unstringify_data(value))
            else:
                new.append(uiqt.unstringify(value))
        
        if isinstance(data,tuple):
            new=tuple(new)
        elif isinstance(data,set):
            new=set(new)
        return(new)

def wrap_data(data):
    data = stringify_data(data)
    data = json.dumps(data)
    #data = zlib.compress(data.encode("utf-8"), level=9)
    return(data)
def unwrap_data(data):
    #data = zlib.decompress(data).decode("utf-8")
    data = json.loads(data)
    data = unstringify_data(data)
    return(data)

def is_floatable(string):
    return(string.removeprefix("-").replace(".","",1).isdecimal())
def is_intable(string):
    return(string.removeprefix("-").isdecimal())
#
def chunkify(_list, chunk_size):
    for i in range(0, len(_list), chunk_size):
        yield(_list[i:i+chunk_size])
#
def condense_ipgs(inputPaths, outputPath):
    with gzip.open(outputPath, mode="wt") as output:
        output.write("<IPGSet>\n")
        for inputPath in inputPaths:
            with gzip.open(inputPath, mode="rt") as input:
                write = False
                for line in input:
                    #if line[:10] == "<IPGReport": #IPGSETSET
                    if ("<IPGReport " in line): #TODO: does xml use \t instead of space?
                        write = True
                        line = line.split("<IPGReport")[-1]
                        output.write("<IPGReport"+line)
                    elif "</IPGReport>" in line:
                        write = False
                        line = line.split("</IPGReport>")[0]
                        output.write(line+"</IPGReport>\n")
                    elif write:
                        output.write(line)
                    #/Transfer
                    #if line[-13:] == "</IPGReport>\n":
        output.write("</IPGSet>\n")
        output.flush()
#
def load_blastp_xmls(handles):
    # For loading the BLASTP results data, we just use the default
    #   biopython record classes and hang some of our own variables
    #   on top of them so they can be used in the data structure.
    #
    # record.als is a dict of alignments by protein accession
    #   I'd put this into record.alignments, but I'm a little scared
    #   to break compatibility with the original data structure,
    #   just in case.
    def facc(accession):
        return(accession.split(".")[0])
    records = {}
    for handle in handles:
        # I think the NCBI BLAST output ädds non-xml garbage to signal information
        #   to the web data viewer, but biopython's XML parser doesn't know
        #   how to process it so it crashes.
        
        file = NCBIXML.parse(handle)
        fasta_blast = False
        for record in file:
            record.query_id = facc(record.query_id)
            record.als = {}
            #Check if this is blast is derived from a 
            #   multifasta database, using this hack:
            try:
                if "subject" in record.alignments[0].accession.lower():
                    #If so, flip a flag
                    fasta_blast = True
            except IndexError:
                print("Error! Record contains no alignments!!")
                if ERROR_MANAGER:
                    ERROR_MANAGER.sig_no_alignments.emit()
            else:
                for alignment in record.alignments:
                    if fasta_blast or alignment.accession=="unnamed protein":
                        #If this is a fasta_blast, the sequence identifiers
                        #   will be found in a different field:
                        alignment.accession = facc(alignment.hit_id)
                    else:
                        alignment.accession = facc(alignment.accession)
                    #Set up links to record and protein
                    alignment.record = record
                    alignment.pt = None
                    #
                    record.als[alignment.accession] = alignment
                    alignment.tophsp = max(alignment.hsps, 
                                           key=lambda hsp: hsp.score)
                records[record.query_id] = record
        file.close()
    return(records)
#
def download_ncbi(filepath=None, id=None, chunksize=500, verbose=True, into_file=True, **kwargs):
    if filepath is None and into_file is True:
        raise ValueError("Argument \"filepath\" is unspecified or None. Requires a path str (Eg. C:/thing.txt).")
    if id is None:
        raise ValueError("Argument \"id\" is unspecified or None. Use a list of GenBank accession codes.")
    accessions = id #Confusion bonus
    
    #How many full-sized accession blocks to expect
    #  There will usually be one final chunk that's smaller than chunksize
    nchunks = math.floor(len(accessions)/chunksize)
    querychunks=[] #The blocks of accessions we'll iterate over
    
    XML = False
    if kwargs["retmode"] == "xml":
        XML = True
    
    last = 0
    for i in range(0, nchunks):
        #Compose our chunks into strings
        last = ((i+1)*chunksize)
        querychunks.append(",".join(accessions[i*chunksize:last]))
    # - Add final chunk to fill in the rest
    if len(accessions) > last:
        querychunks.append(",".join(accessions[last:len(accessions)]))
    
    # - - - Start writing our output file.
    #maybe don't do this, people can name their stuff what they like:
    #if ".gz" not in filepath:
    #    filepath+=".gz"
    first=True
    #with gzip.open(filepath, mode="wt") as output:
    output = io.StringIO()
    if verbose:
        print("Opened file at {}\n".format(filepath))
    #IF XML
    if XML:
        #TODO: Deleting header and inserting our own is hacky, fix later
        output.write("<?xml version=\"1.0\" encoding=\"UTF-8\"  ?>\n")
        output.write("<ReportSetSet>\n")
    #IF OTHER
        #TODO: Fill in other modes if needed.
    #Now iterate the requests
    i=0
    imax = len(querychunks)
    while i < imax: #We're using while to facilitate retries
        # abort is a signal from Download Manager as to whether we should
        #   interrupt the download for some reason.
        
        chunkcontent = [] #We'll save the chunk into this variable
        #Save the chunk into memory in case transfer fails
        time.sleep(0.1)
        chunk = querychunks[i]
        if verbose:
            print("Downloading {}-long chunk {}/{}...\r".format(len(chunk.split(",")),i+1,imax))
        #try:
        try:
            handle = Entrez.efetch(id=chunk, **kwargs)
            for line in handle:
                line = line.decode("utf-8")
                if ((XML) and ("<?xml" in line)):
                    continue
                chunkcontent.append(line)
            i+=1
        except:
            if verbose:
                print("Failed, retrying...")
            continue
            #The transfer failed, do not increment i, which will result in a retry next iteration
        for line in chunkcontent:
            output.write(line)
        #abort = DOWNLOAD_MANAGER.download_status(
        #    number_left_to_download=(imax-i)*chunksize)
    if XML:
        output.write("\n</ReportSetSet>\n")
    output.flush()
    output.seek(0)
    if verbose:
        print("Download complete.")
    #DOWNLOAD_MANAGER.download_ended()
    if into_file:
        with gzip.open(filepath, mode="wt") as outfile:
            outfile.write(output)
            outfile.flush()
            outfile.close()
        return(filepath)
    else:
        return(output)
#
def download_neighbors(inputs, folder=None, verbose=True, **kwargs):
    #This function is derived from download_ncbi, but is built for a specific purpose
    #input should be a list of tuples in the format (nucletoide_id, start, stop)
    # EG: inputs = [(id1, 200, 500), (id2, 800, 1200), (id3, 0, 300)]
    if folder is None:
        raise ValueError("Argument \"folder\" is unspecified or None. Requires a path str (Eg. C:/thing.txt).")
    db="nuccore"
    rettype="fasta_cds_aa"
    retmode="text"
        
    #Initialize verbose mode variables    
    verbosemax = 1
    verbosei = 0
    #The goal is to avoid spamming the output when too many files are downloaded
    #The verbose output reports less and less frequently the more iterations it's gone through
    
    # - - - Start writing our output file.
    #maybe don't do this, people can name their stuff what they like:
    #if ".gz" not in filepath:
    #    filepath+=".gz"
    first=True
    i=0
    imax = len(inputs)
    with open(folder+"_index.txt", mode="w") as indexfile:
        while i < imax: #We're using while to facilitate retries
            #Save the chunk into memory until the transfer completes
            time.sleep(0.1)
            if verbose:
                #see verbosemax/i explanation above
                verbosei += 1
                if verbosei==verbosemax:
                    print("Downloading neighbourhood {}/{}...".format(i+1,imax+1))
                    verbosei = 0
                    verbosemax = verbosemax + 1 + math.floor(verbosemax*0.2)
            #Unpack the input
            id,start,stop = inputs[i]
            filepath = folder+"{}_{}-{}.gb.gz".format(id,start,stop)
            try:
                chunk = []
                handle = Entrez.efetch(id=id, db="nuccore", rettype="gb", 
                                       retmode="xml", seq_start=start, 
                                       seq_stop=stop, **kwargs)
                #store the downloaded genbank file in memory
                for line in handle:
                    line = line.decode("utf-8")
                    chunk.append(line)
                #once the download is complete, save the file
                with gzip.open(filepath, mode="wt") as output:
                    #May need to use mode="wt" if the handle returns strings
                    for line in chunk:
                        output.write(line)
                i+=1
                #also add the file to the index
                indexfile.write("{}\t{}\t{}\t{}\n".format(id,start,stop,filepath))
            except:
                if verbose:
                    print("Failed, retrying...")
                continue
            #    #The transfer failed, just try again
        return(filepath)
def download_neighbors_old(inputs, filepath=None, verbose=True, **kwargs):
    #This function is derived from download_ncbi, but is built for a specific purpose
    #input should be a list of tuples in the format (nucletoide_id, start, stop)
    # EG: inputs = [(id1, 200, 500), (id2, 800, 1200), (id3, 0, 300)]
    if filepath is None:
        raise ValueError("Argument \"filepath\" is unspecified or None. Requires a path str (Eg. C:/thing.txt).")
    db="nuccore"
    rettype="fasta_cds_aa"
    retmode="text"
    
    
    XML = True
        
    #Initialize verbose mode variables    
    verbosemax = 1
    verbosei = 0
    #The goal is to avoid spamming the output when too many files are downloaded
    #The verbose output reports less and less frequently the more iterations it's gone through
    
    # - - - Start writing our output file.
    #maybe don't do this, people can name their stuff what they like:
    #if ".gz" not in filepath:
    #    filepath+=".gz"
    first=True
    with gzip.open(filepath, mode="wt") as output:
        if verbose:
            print("Opened file at {}".format(filepath))
        if XML:
            #TODO: Deleting header and inserting our own is hacky, fix later
            output.write("<?xml version=\"1.0\" encoding=\"UTF-8\"  ?>\n")
            output.write("<ReportSetSet>\n")
        #IF OTHER
            #TODO: Fill in other modes if needed.
        #Now iterate the requests
        i=0
        imax = len(inputs)
        while i < imax: #We're using while to facilitate retries
            chunkcontent = [] #We'll save the chunk into this variable
            #Save the chunk into memory until the transfer completes
            time.sleep(0.1)
            if verbose:
                #see verbosemax/i explanation above
                verbosei += 1
                if verbosei==verbosemax:
                    print("Downloading neighbourhood {}/{}...".format(i+1,imax+1))
                    verbosei = 0
                    verbosemax = verbosemax + 1 + math.floor(verbosemax*0.2)
            #Unpack the input
            id,start,stop = inputs[i]
            try:
                handle = Entrez.efetch(id=id, db="nuccore", rettype="gb", retmode="xml", seq_start=start, 
                                       seq_stop=stop, **kwargs)
                for line in handle:
                    if ((XML) and ("<?xml" in line)):
                        continue
                    elif ((XML) and ("<!DOCTYPE" in line)):
                        continue
                    chunkcontent.append(line)
                i+=1
            except:
                if verbose:
                    print("Failed, retrying...")
                continue
                #The transfer failed, just try again
            for line in chunkcontent:
                output.write(line)
        if XML:
            output.write("\n</ReportSetSet>\n")
        output.flush()
        output.close()
        if verbose:
            print("Complete. Downloaded {}/{} files.".format(i+1, imax+1))
    return(filepath)
#
def parse_ipgxml_basic(handle):
    #Iterates through an ipgxml and returns a dict of values 
    #   for each coding sequence(cds)
    
    #XML parsing loop:
    for event, elem in ET.iterparse(handle, events=("start",)):
        if elem.tag == "CDS":
            feature = {
                "fttype": "cds",
                "ftstart": int(elem.get("start")),
                "ftstop": int(elem.get("stop")),
                "ftstrand": elem.get("strand"),
                "ptacc": ptAcc.split(".")[0],
                "ptver": ptAcc.split(".")[1],
                "ptname": ptName,
                "iptacc": iptAcc,
                "sciname": elem.get("org"),
                "scacc": elem.get("accver").split(".")[0],
                "scver": elem.get("accver").split(".")[1],
                "taxid": elem.get("taxid"),
                "taxstrain": elem.get("strain"),
            }
            yield(feature)
        elif elem.tag == "CDSList":
            pass
        elif elem.tag == "Protein":
            ptName = elem.get("name")
            ptAcc = elem.get("accver")
        elif elem.tag == "ProteinList":
            pass
        elif elem.tag == "IPGReport":
            iptAcc = elem.get("ipg")
        else:
            pass
#
def build_data_tree(ftdicts, root=None): #build_ipg_tree
    if root is None:
        root = dframe.Root()
    
    duplicateFeatures = 0
    
    for ftdict in ftdicts:
        #get taxon
        taxstrid = f'{ftdict["taxid"]}:{ftdict["taxstrain"]}'
        if taxstrid in root.txAll:
            tx = root.txAll[taxstrid]
        else:
            tx = dframe.Taxon(
                ftdict["taxid"], root, sciname=ftdict["sciname"],
                strain=ftdict["taxstrain"])
        #get scaffold
        if ftdict["scacc"] in root.scAll:
            sc = root.scAll[ftdict["scacc"]]
        else:
            sc = dframe.Scaffold(
                accession=ftdict["scacc"], taxon=tx,
                version=ftdict["scver"])
        #get ipt
        if ftdict["iptacc"] in root.iptAll:
            ipt = root.iptAll[ftdict["iptacc"]]
        else:
            ipt = dframe.IdenticalProteinSet(ftdict["iptacc"], root)
        #get protein
        if ftdict["ptacc"] in root.ptAll:
            pt = root.ptAll[ftdict["ptacc"]]
        else:
            pt = dframe.Protein(
                accession=ftdict["ptacc"], 
                version=ftdict["ptver"],
                iprotein=ipt, 
                name=ftdict["ptname"])
        #finally, make feature
        if ftdict["scacc"] in pt.fts:
            duplicateFeatures += 1
        #if ftdict["ftstrand"] == "+":
        #    ftdict["ftstrand"] = dframe.Strand.PRIMARY
        #elif ftdict["ftstrand"] == "-":
        #    ftdict["ftstrand"] = dframe.Strand.COMPLEMENTARY
        ft = dframe.Feature(scaffold=sc, 
                            reference=pt, 
                            start=ftdict["ftstart"], 
                            stop=ftdict["ftstop"],
                            fttype=ftdict["fttype"],
                            strand=ftdict["ftstrand"])
    return(root)
#
#TODO: Add bioproject, biosample, taxonomy etc. to scaffolds and taxa where appropriate.
def update_scs_with_gbdata(gbrecord, region, root, types_=None):
    if gbrecord["scacc"] not in root.scAll:
        print("Sequence accession not found in root! Skipping...")
        return(False)
    sc = root.scAll.get(gbrecord["scacc"])
    # Update sc
    sc.annotations = {
        "taxonomy": gbrecord["taxonomy"],
        "topology": gbrecord["topology"],
        "references": gbrecord["references"],
        "comment": gbrecord["comment"]
    }
    region.seq = gbrecord["regseq"]
    #region.stop = region.start + len(region.seq)
    
    
    # Update fts
    for rawfeature in gbrecord["features"]:
        if types_ is not None and rawfeature["fttype"] not in types_:
            continue
        if rawfeature["fttype"] == "cds":
            if rawfeature["ptacc"] is None:
                #Sometimes pseudogenes get a CDS
                # with a nonexistent protein.
                # -- it's not actually a coding sequence, so it gets ignored.
                continue
            #Trim the version number from the accession
            rawfeature["ptacc"] = rawfeature["ptacc"]\
                .split(".")[0]
            
            
            #Build protein/iprotein if they're missing
            #   We don't know which proteins are identical,
            #   so we just set up an iprotein for each protein.
            if rawfeature["ptacc"] not in root.ptAll:
                # If protein doesn't exist, make an ipt and pt for it
                
                ipt = dframe.IdenticalProteinSet(
                    rawfeature["ptacc"], root)
                
                pt = dframe.Protein(
                    rawfeature["ptacc"],
                    rawfeature["ptver"],
                    ipt, 
                    seq=rawfeature["ptseq"], 
                    name=rawfeature["ptacc"], 
                    type=rawfeature["pttype"])
            else:
                # Otherwise, just grab it and update it
                pt = root.ptAll[rawfeature["ptacc"]]
                
                pt.seq = rawfeature["ptseq"]
                pt.type = rawfeature["pttype"]
                
                #Leaving this out because it's likely already been set
                #pt.name = rawfeature["ptacc"]
            if rawfeature["ptacc"] not in sc.fts:
                # If the protein's CDS isn't in the scaffold yet, add it
                dframe.Feature(scaffold=sc, 
                               reference=pt, 
                               start=rawfeature["ftstart"], 
                               stop=rawfeature["ftstop"], 
                               fttype=rawfeature["fttype"],
                               strand=rawfeature["ftstrand"])
#
def frozen_path(mypath):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)