from .collections import SMessage
#==========================================================================================================================================

class Mongodb:

    async def clean(database, pipeline, coun01=0, coun02=0):
        async for docum in database.aggregate(pipeline):
            domuid = docum["ids"][1:]
            result = await database.delete_many( {"_id": {"$in": domuid} } )
            coun01 += int(result.deleted_count)
            coun02 += 1

        return SMessage(numfiles=coun01, numusers=coun02)

#==========================================================================================================================================

    async def regexs(filters="$id"):
        return [ {"$group": {"_id": filters, "count": {"$sum": 1}, "ids": {"$push": "$_id"} } }, {"$match": {"count": {"$gt": 1} } } ]

#==========================================================================================================================================
