import warnings
from asyncio import run
from puresnmp import Client, V2C, PyWrapper
from puresnmp import ObjectIdentifier as OID
from puresnmp.exc import NoSuchOID, SnmpError
from collections import defaultdict 
from x690.types import *
from typing import Literal
# from puresnmp_olt.tools import ascii_to_hex
from tools import ascii_to_hex


#Get data
def Get(host: str, community: str, oid: str):
    try:
        warnings.simplefilter("ignore")
        client = PyWrapper(Client(host, V2C(community)))
        value = client.get(oid)
        response = run(value)

        return oid,response
    except NoSuchOID: # Catch NoSuchOID specifically
        print({"Cod":404, "Message": "No such name/oid"}) # Use the specific message
        return {
                "Cod":404,
                "Message":"No such name/oid"
            }
    except Exception as e: # Catch other exceptions
        print(f"An unexpected error occurred: {e}")
        return {
            "Cod": 500,
            "Message": f"An unexpected error occurred: {e}"
        }
    
#Get data in async
async def Get_async(host: str, community: str, oid: str):
    try:
        warnings.simplefilter("ignore")
        client = PyWrapper(Client(host, V2C(community)))
        value = await client.get(oid)

        return oid,value
    except NoSuchOID:
        print({"Cod":NoSuchOID.DEFAULT_MESSAGE})
        return {
                "Cod":404,
                "Message":NoSuchOID.DEFAULT_MESSAGE
            }
    except Exception as e: # Catch other exceptions
        print(f"An unexpected error occurred: {e}")
        return {
            "Cod": 500,
            "Message": f"An unexpected error occurred: {e}"
        }
    
#Get data next
def GetNext(host: str, community: str, oid: str):
    try:
        warnings.simplefilter("ignore")
        client = PyWrapper(Client(host, V2C(community)))
        value = client.getnext(oid)
        response = run(value)

        return oid,response[1]
    except NoSuchOID:
        print({"Cod":NoSuchOID.DEFAULT_MESSAGE})
        return {
                "Cod":404,
                "Message":NoSuchOID.DEFAULT_MESSAGE
            }
    except Exception as e: # Catch other exceptions
        print(f"An unexpected error occurred: {e}")
        return {
            "Cod": 500,
            "Message": f"An unexpected error occurred: {e}"
        }
    
#Get data next
async def GetNext_async(host: str, community: str, oid: str):
    try:
        warnings.simplefilter("ignore")
        client = PyWrapper(Client(host, V2C(community)))
        value = await client.getnext(oid)

        return value[0],value[1]
    except NoSuchOID:
        print({"Cod":NoSuchOID.DEFAULT_MESSAGE})
        return {
                "Cod":404,
                "Message":NoSuchOID.DEFAULT_MESSAGE
            }
    except Exception as e: # Catch other exceptions
        print(f"An unexpected error occurred: {e}")
        return {
            "Cod": 500,
            "Message": f"An unexpected error occurred: {e}"
        }

#MultiGet data
def MultiGet(host: str, community: str, oid: list[str]):
    data = []
    try:
        warnings.simplefilter("ignore")
        client = PyWrapper(Client(host, V2C(community)))
        value = client.multiget(oid)
        response = run(value)
        if response is not None:
            for x in range(len(oid)):
                data.append({"oid":oid[x],
                        "value":response[x]})
        return data
    except NoSuchOID:
        print({"Cod":NoSuchOID.DEFAULT_MESSAGE})
        return {
                "Cod":404,
                "Message":NoSuchOID.DEFAULT_MESSAGE
            }
    except Exception as e: # Catch other exceptions
        print(f"An unexpected error occurred: {e}")
        return {
            "Cod": 500,
            "Message": f"An unexpected error occurred: {e}"
        }
    
#MULTIWALK is necesary execute with run of "from asyncio import run" examp = run(MultiTask(...)) 
async def MultiWalk_async(host: str, community: str, oid: list[str],only_final_id=False,decode_ascii=False):
    try:
        data = []
        warnings.simplefilter("ignore")
        client = PyWrapper(Client(host, V2C(community)))
        async for row in client.multiwalk(oid):
            if decode_ascii:
                decode = ascii_to_hex(row[1])
            else:
                decode = row[1]

            if only_final_id:
                data.append({"oid": row[0].split(".")[-1], "value": decode})  
            else:
                data.append({"oid": row[0], "value": decode}) 
        return data
    except NoSuchOID:
        print({"Cod":NoSuchOID.DEFAULT_MESSAGE})
        return {
                "Cod":404,
                "Message":NoSuchOID.DEFAULT_MESSAGE
            }
    except Exception as e: # Catch other exceptions
        print(f"An unexpected error occurred: {e}")
        return {
            "Cod": 500,
            "Message": f"An unexpected error occurred: {e}"
        }
    
#MULTIWALK is necesary execute with run of "from asyncio import run" examp = run(Walk_async(...)) 
async def Walk_async(host: str, community: str, oid: str,only_final_id=False,decode_ascii=False):
    try:
        data = []
        warnings.simplefilter("ignore")
        client = PyWrapper(Client(host, V2C(community)))
        async for row in client.walk(oid):
            if decode_ascii:
                decode = ascii_to_hex(row[1])
            else:
                decode = row[1]

            if only_final_id:
                data.append({"oid": row[0].split(".")[-1], "value": decode})  
            else:
                data.append({"oid": row[0], "value": decode}) 
        return data
    except NoSuchOID:
        print({"Cod":NoSuchOID.DEFAULT_MESSAGE})
        return {
                "Cod":404,
                "Message":NoSuchOID.DEFAULT_MESSAGE
            }
    except Exception as e: # Catch other exceptions
        print(f"An unexpected error occurred: {e}")
        return {
            "Cod": 500,
            "Message": f"An unexpected error occurred: {e}"
        }
    
def MultiWalk(host: str, community: str, oid: list[str], only_final_id=False, decode_ascii=False):
    try:
        warnings.simplefilter("ignore")
        # PyWrapper es la API de alto nivel
        client = PyWrapper(Client(host, V2C(community)))

        async def _inner_multiwalk_runner():
            data = []
            # Pasamos la lista de OIDs como strings directamente a PyWrapper
            # No es necesario convertirlos a OID() manualmente aquí.
            async for row in client.multiwalk(oid):
                # La fila (row) contendrá un OID como objeto y su valor
                # Podemos convertir el OID a string para el diccionario de salida
                data.append({"oid": str(row[0]), "value": row[1]})
            return data

        return run(_inner_multiwalk_runner())
    except SnmpError as e: # Capturamos SnmpError para errores específicos de la librería
        print({"Error SNMP": str(e)})
        return {
                "Cod":404,
                "Message": f"Error en la operación MultiWalk: {str(e)}"
            }
    except Exception as e: # Capturamos cualquier otra excepción
        print({"Error general": str(e)})
        return {
                "Cod":404,
                "Message": f"Error inesperado: {str(e)}"
            }

#Set data in snmp 
def Set(host: str, community: str, oid: str,new_value,_type: Literal["int", "Oct"] = "int"):
        types = {
            "int":Integer,
            "Oct":OctetString
        }
        try:
            warnings.simplefilter("ignore")
            client = Client(host, V2C(community))
            value = client.set(OID(oid),types[_type](new_value))
            response = run(value)
            return{
                "Cod":200,
                "Message":f"Change to {new_value}"
            }
        except NoSuchOID:
            print({"Cod":NoSuchOID.DEFAULT_MESSAGE})
            return {
                "Cod":404,
                "Message":NoSuchOID.DEFAULT_MESSAGE
            }
        except Exception as e: # Catch other exceptions
            print(f"An unexpected error occurred: {e}")
            return {
            "Cod": 500,
            "Message": f"An unexpected error occurred: {e}"
        }

#Set data in async
async def Set_async(host: str, community: str, oid: str,new_value,_type: Literal["int", "Oct"] = "int"):
    types = {
            "int":Integer,
            "Oct":OctetString
        }
    try:
        warnings.simplefilter("ignore")
        client = PyWrapper(Client(host, V2C(community)))
        value = await client.set(oid,types[_type](new_value))

        return{
                "Cod":200,
                "Message":f"{value}"
            }
    except NoSuchOID:
        print({"Cod":NoSuchOID.DEFAULT_MESSAGE})
        return {
                "Cod":404,
                "Message":NoSuchOID.DEFAULT_MESSAGE
            }
    except Exception as e: # Catch other exceptions
        print(f"An unexpected error occurred: {e}")
        return {
            "Cod": 500,
            "Message": f"An unexpected error occurred: {e}"
        }
    

###In working ################################
#MultiSet data in snmp 
def MultiSet(host: str, community: str, oid: str,new_value,_type: Literal["int", "Oct"] = "int"):
        types = {
            "int":Integer,
            "Oct":OctetString
        }
        try:
            warnings.simplefilter("ignore")
            client = Client(host, V2C(community))
            value = client.set(OID(oid),types[_type](new_value))
            response = run(value)

            return ({"Change to":new_value})
        except NoSuchOID:
            print({"Cod":NoSuchOID.DEFAULT_MESSAGE})
            return {
                "Cod":404,
                "Message":NoSuchOID.DEFAULT_MESSAGE
            }
        except Exception as e: # Catch other exceptions
            print(f"An unexpected error occurred: {e}")
            return {
            "Cod": 500,
            "Message": f"An unexpected error occurred: {e}"
        }






# def Table(host: str, community: str, oid: str):
#     data = []
    
#     warnings.simplefilter("ignore")
#     client = PyWrapper(Client(host, V2C(community)))
#     value = client.table(oid)
#     response = run(value)
#     if response is not None:
#         for x in range(len(response)):
#             for id,value in response[x]:
#                 print(value)
#     return "ff"
