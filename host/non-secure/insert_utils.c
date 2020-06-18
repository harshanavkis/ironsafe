#include "insert_utils.h"

VdbeCursor *OpenWriteTable(VdbeCursor *pCur, sqlite3 *db, int ndp_Db, int ndp_rootpage, int cur_name, int n_cols)
{
	Btree *pX;
	Db *pDb;
	int wrFlag;
	int p2;
	int nField;
	int iDb;
	KeyInfo *pKeyInfo;

	int rc;

	nField = 0;
	pKeyInfo = 0;
	p2  = ndp_rootpage;
	iDb = ndp_Db;
	pDb = &db->aDb[iDb];
	pX  = pDb->pBt;

	wrFlag = BTREE_WRCSR | (pOp->p5 & OPFLAG_FORDELETE);
	assert( sqlite3SchemaMutexHeld(db, iDb, 0) );

	nField = n_cols;

	pCur = allocateCursor(p, cur_name, nField, iDb, CURTYPE_BTREE);

	pCur->nullRow = 1;
	pCur->isOrdered = 1;
	pCur->pgnoRoot = p2;

	rc = sqlite3BtreeCursor(pX, p2, wrFlag, pKeyInfo, pCur->uc.pCursor);
	
	if(rc)
		return NULL;

	pCur->pKeyInfo = pKeyInfo;
	pCur->isTable = 1;

	return pCur;
}

i64 GetNewRowid(VdbeCursor *pC)
{
	i64 v;
	int res;
	int cnt;
	Mem *pMem;

	v = 0;
	res = 0;

	assert( pC!=0 );
	assert( pC->isTable );
	assert( pC->eCurType==CURTYPE_BTREE );
	assert( pC->uc.pCursor!=0 );
  {
    /* The next rowid or record number (different terms for the same
    ** thing) is obtained in a two-step algorithm.
    **
    ** First we attempt to find the largest existing rowid and add one
    ** to that.  But if the largest existing rowid is already the maximum
    ** positive integer, we have to fall through to the second
    ** probabilistic algorithm
    **
    ** The second algorithm is to select a rowid at random and see if
    ** it already exists in the table.  If it does not exist, we have
    ** succeeded.  If the random rowid does exist, we select a new one
    ** and try again, up to 100 times.
    */
    assert( pC->isTable );

#ifdef SQLITE_32BIT_ROWID
#   define MAX_ROWID 0x7fffffff
#else
    /* Some compilers complain about constants of the form 0x7fffffffffffffff.
    ** Others complain about 0x7ffffffffffffffffLL.  The following macro seems
    ** to provide the constant while making all compilers happy.
    */
#   define MAX_ROWID  (i64)( (((u64)0x7fffffff)<<32) | (u64)0xffffffff )
#endif

    if( !pC->useRandomRowid ){
      rc = sqlite3BtreeLast(pC->uc.pCursor, &res);
      if( rc!=SQLITE_OK ){
        return -1;
      }
      if( res ){
        v = 1;   /* IMP: R-61914-48074 */
      }else{
        assert( sqlite3BtreeCursorIsValid(pC->uc.pCursor) );
        v = sqlite3BtreeIntegerKey(pC->uc.pCursor);
        if( v>=MAX_ROWID ){
          pC->useRandomRowid = 1;
        }else{
          v++;   /* IMP: R-29538-34987 */
        }
      }
    }

    if( pC->useRandomRowid ){
      /* IMPLEMENTATION-OF: R-07677-41881 If the largest ROWID is equal to the
      ** largest possible integer (9223372036854775807) then the database
      ** engine starts picking positive candidate ROWIDs at random until
      ** it finds one that is not previously used. */
      assert( pOp->p3==0 );  /* We cannot be in random rowid mode if this is
                             ** an AUTOINCREMENT table. */
      cnt = 0;
      do{
        sqlite3_randomness(sizeof(v), &v);
        v &= (MAX_ROWID>>1); v++;  /* Ensure that v is greater than zero */
      }while(  ((rc = sqlite3BtreeMovetoUnpacked(pC->uc.pCursor, 0, (u64)v,
                                                 0, &res))==SQLITE_OK)
            && (res==0)
            && (++cnt<100));
      if( rc ) goto abort_due_to_error;
      if( res==0 ){
        rc = SQLITE_FULL;   /* IMP: R-38219-53002 */
        goto abort_due_to_error;
      }
      assert( v>0 );  /* EV: R-40812-03570 */
    }
    pC->deferredMoveto = 0;
    pC->cacheStatus = CACHE_STALE;
  }

  return v;
}

int InsertRecord(sqlite3 *db, i64 v, Mem *pData, VdbeCursor *pC)
{
  int seekResult;
  const char *zDb;
  Table *pTab;
  BtreePayload x;
  int rc;

  x.nKey = v;
  pTab = 0;
  zDb = 0;
  assert( pData->flags & (MEM_Blob|MEM_Str) );
  x.pData = pData->z;
  x.nData = pData->n;
  seekResult = 0;
  if( pData->flags & MEM_Zero ){
    x.nZero = pData->u.nZero;
  }else{
    x.nZero = 0;
  }
  x.pKey = 0;
  rc = sqlite3BtreeInsert(pC->uc.pCursor, &x,
      (0 & (OPFLAG_APPEND|OPFLAG_SAVEPOSITION)), seekResult);
  pC->deferredMoveto = 0;
  pC->cacheStatus = CACHE_STALE;

  return rc;
}

int AddRawRecord(sqlite3 *db, Mem *pData, int ndp_Db, int ndp_rootpage, int n_cols)
{
  int cur_name = 1;
  VdbeCursor *pCur;
  i64 v;
  int rc;

  pCur = OpenWriteTable(VdbeCursor *pCur, db, ndp_Db, ndp_rootpage, cur_name, n_cols);
  if(!pCur)
    return -1;
  v    = GetNewRowid(pCur);
  rc = InsertRecord(db, v, pData, pCur);

  return rc;
}
