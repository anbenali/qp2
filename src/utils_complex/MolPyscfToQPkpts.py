import numpy as np
from functools import reduce


def memoize(f):
    memo = {}
    def helper(x):
        if x not in memo:
            memo[x] = f(x)
        return memo[x]
    return helper

@memoize
def idx2_tri(iijj):
    '''
    iijj should be a 2-tuple
    return triangular compound index for (0-indexed counting)
    '''
    ij1=min(iijj)
    ij2=max(iijj)
    return ij1+(ij2*(ij2+1))//2
#    return ij1+(ij2*(ij2-1))//2

def pad(arr_in,outshape):
    arr_out = np.zeros(outshape,dtype=np.complex128)
    dataslice = tuple(slice(0,arr_in.shape[dim]) for dim in range(len(outshape)))
    arr_out[dataslice] = arr_in
    return arr_out

def idx40(i,j,k,l):
    return idx2_tri((idx2_tri((i,k)),idx2_tri((j,l))))

def idx4(i,j,k,l):
    return idx2_tri((idx2_tri((i-1,k-1)),idx2_tri((j-1,l-1))))+1

def stri4(i,j,k,l):
    return (4*'{:5d}').format(i,j,k,l)

def stri4z(i,j,k,l,zr,zi):
    return (4*'{:5d}'+2*'{:25.16e}').format(i,j,k,l,zr,zi)

def stri2z(i,j,zr,zi):
    return (2*'{:5d}'+2*'{:25.16e}').format(i,j,zr,zi)

def strijklikjli4z(i,j,k,l,zr,zi):
    return ('{:10d}'+ 2*'{:8d}'+4*'{:5d}'+2*'{:25.16e}').format(idx4(i,j,k,l),idx2_tri((i-1,k-1))+1,idx2_tri((j-1,l-1))+1,i,j,k,l,zr,zi)


def makesq(vlist,n1,n2):
    '''
    make hermitian matrices of size (n2 x n2) from from lower triangles
    vlist is n1 lower triangles in flattened form
    given: ([a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t],2,4)
           output a 2x4x4 array, where each 4x4 is the square constructed from the lower triangle
    [
     [
      [a  b* d* g*]
      [b  c  e* h*]
      [d  e  f  i*]
      [g  h  i  j ]
     ],
     [
      [k  l* n* q*]
      [l  m  o* r*]
      [n  o  p  s*]
      [q  r  s  t ]
     ]
    ]
    '''
    out=np.zeros([n1,n2,n2],dtype=np.complex128)
    n0 = vlist.shape[0]
    lmask=np.tri(n2,dtype=bool)
    for i in range(n0):
        out[i][lmask] = vlist[i].conj()
    out2=out.transpose([0,2,1])
    for i in range(n0):
        out2[i][lmask] = vlist[i]
    return out2


def makesq3(vlist,n2):
    '''
    make hermitian matrices of size (n2 x n2) from from lower triangles
    vlist is n1 lower triangles in flattened form
    given: ([a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t],2,4)
           output a 2x4x4 array, where each 4x4 is the square constructed from the lower triangle
    [
     [
      [a  b* d* g*]
      [b  c  e* h*]
      [d  e  f  i*]
      [g  h  i  j ]
     ],
     [
      [k  l* n* q*]
      [l  m  o* r*]
      [n  o  p  s*]
      [q  r  s  t ]
     ]
    ]
    '''
    n0 = vlist.shape[0]
    out=np.zeros([n0,n2,n2],dtype=np.complex128)
    lmask=np.tri(n2,dtype=bool)
    for i in range(n0):
        out[i][lmask] = vlist[i].conj()
    out2=out.transpose([0,2,1])
    for i in range(n0):
        out2[i][lmask] = vlist[i]
    return out2

def makesq2(vlist,n1,n2):
    out=np.zeros([n1,n2,n2],dtype=np.complex128)
    lmask=np.tri(n2,dtype=bool)
    tmp=np.zeros([n2,n2],dtype=np.complex128)
    tmp2=np.zeros([n2,n2],dtype=np.complex128)
    for i in range(n1):
        tmp[lmask] = vlist[i].conj()
        tmp2=tmp.T
        tmp2[lmask] = vlist[i]
        out[i] = tmp2.copy()
    return out


def get_phase(cell, kpts, kmesh=None):
    '''
    The unitary transformation that transforms the supercell basis k-mesh
    adapted basis.
    '''
    from pyscf.pbc import tools
    from pyscf import lib

    latt_vec = cell.lattice_vectors()
    if kmesh is None:
        # Guess kmesh
        scaled_k = cell.get_scaled_kpts(kpts).round(8)
        kmesh = (len(np.unique(scaled_k[:,0])),
                 len(np.unique(scaled_k[:,1])),
                 len(np.unique(scaled_k[:,2])))

    R_rel_a = np.arange(kmesh[0])
    R_rel_b = np.arange(kmesh[1])
    R_rel_c = np.arange(kmesh[2])
    R_vec_rel = lib.cartesian_prod((R_rel_a, R_rel_b, R_rel_c))
    R_vec_abs = np.einsum('nu, uv -> nv', R_vec_rel, latt_vec)

    NR = len(R_vec_abs)
    phase = np.exp(1j*np.einsum('Ru, ku -> Rk', R_vec_abs, kpts))
    phase /= np.sqrt(NR)  # normalization in supercell

    # R_rel_mesh has to be construct exactly same to the Ts in super_cell function
    scell = tools.super_cell(cell, kmesh)
    return scell, phase

def mo_k2gamma(cell, mo_energy, mo_coeff, kpts, kmesh=None):
    '''
    Transform MOs in Kpoints to the equivalents supercell
    '''
    from pyscf import lib
    import scipy.linalg as la
    scell, phase = get_phase(cell, kpts, kmesh)

    E_g = np.hstack(mo_energy)
    C_k = np.asarray(mo_coeff)
    Nk, Nao, Nmo = C_k.shape
    NR = phase.shape[0]

    # Transform AO indices
    C_gamma = np.einsum('Rk, kum -> Rukm', phase, C_k)
    C_gamma = C_gamma.reshape(Nao*NR, Nk*Nmo)

    E_sort_idx = np.argsort(E_g)
    E_g = E_g[E_sort_idx]
    C_gamma = C_gamma[:,E_sort_idx]
    s = scell.pbc_intor('int1e_ovlp')
    assert(abs(reduce(np.dot, (C_gamma.conj().T, s, C_gamma))
               - np.eye(Nmo*Nk)).max() < 1e-7)

    # Transform MO indices
    E_k_degen = abs(E_g[1:] - E_g[:-1]).max() < 1e-5
    if np.any(E_k_degen):
        degen_mask = np.append(False, E_k_degen) | np.append(E_k_degen, False)
        shift = min(E_g[degen_mask]) - .1
        f = np.dot(C_gamma[:,degen_mask] * (E_g[degen_mask] - shift),
                   C_gamma[:,degen_mask].conj().T)
        assert(abs(f.imag).max() < 1e-5)

        e, na_orb = la.eigh(f.real, s, type=2)
        C_gamma[:,degen_mask] = na_orb[:, e>0]

    if abs(C_gamma.imag).max() < 1e-7:
        print('!Warning  Some complexe pollutions in MOs are present')

    C_gamma = C_gamma.real
    if  abs(reduce(np.dot, (C_gamma.conj().T, s, C_gamma)) - np.eye(Nmo*Nk)).max() < 1e-7:
        print('!Warning  Some complexe pollutions in MOs are present')

    s_k = cell.pbc_intor('int1e_ovlp', kpts=kpts)
    # overlap between k-point unitcell and gamma-point supercell
    s_k_g = np.einsum('kuv,Rk->kuRv', s_k, phase.conj()).reshape(Nk,Nao,NR*Nao)
    # The unitary transformation from k-adapted orbitals to gamma-point orbitals
    mo_phase = lib.einsum('kum,kuv,vi->kmi', C_k.conj(), s_k_g, C_gamma)

    return mo_phase

def qp2rename():
    import shutil
    qp2names={}
    qp2names['mo_coef_complex'] = 'C.qp'
    qp2names['bielec_ao_complex'] = 'W.qp'

    qp2names['kinetic_ao_complex'] = 'T.qp'
    qp2names['ne_ao_complex'] = 'V.qp'
    qp2names['overlap_ao_complex'] = 'S.qp'


    for old,new in qp2names.items():
        shutil.move(old,new)
    shutil.copy('e_nuc','E.qp')

def print_mo_bi(mf,kconserv=None,outfilename='W.mo.qp',cas_idx=None,bielec_int_threshold = 1E-8):

    cell = mf.cell
    kpts = mf.kpts
    #nao = mf.cell.nao
    #Nk = kpts.shape[0]
    
    mo_coeff = mf.mo_coeff
    # Mo_coeff actif
    mo_k = np.array([c[:,cas_idx] for c in mo_coeff] if cas_idx is not None else mo_coeff)
  
    Nk, nao, nmo = mo_k.shape

    if (kconserv is None):
        from pyscf.pbc import tools
        kconserv = tools.get_kconserv(cell, kpts)

    with open(outfilename,'w') as outfile:
        for d, kd in enumerate(kpts):
            for c, kc in enumerate(kpts):
                if c > d: break
                #idx2_cd = idx2_tri((c,d))
                for b, kb in enumerate(kpts):
                    if b > d: break
                    a = kconserv[b,c,d]
                    if a > d: continue
                    #if idx2_tri((a,b)) > idx2_cd: continue
                    #if ((c==d) and (a>b)): continue
                    ka = kpts[a]
                    eri_4d_mo_kpt = mf.with_df.ao2mo([mo_k[a], mo_k[b], mo_k[c], mo_k[d]],
                                                      [ka,kb,kc,kd],compact=False).reshape((nmo,)*4)
                    eri_4d_mo_kpt *= 1./Nk
                    for l in range(nmo):
                        ll=l+d*nmo
                        for j in range(nmo):
                            jj=j+c*nmo
                            if jj>ll: break
                            idx2_jjll = idx2_tri((jj,ll))
                            for k in range(nmo):
                                kk=k+b*nmo
                                if kk>ll: break
                                for i in range(nmo):
                                    ii=i+a*nmo
                                    if idx2_tri((ii,kk)) > idx2_jjll: break
                                    if ((jj==ll) and (ii>kk)): break
                                    v=eri_4d_mo_kpt[i,k,j,l]
                                    if (abs(v) > bielec_int_threshold):
                                        outfile.write(stri4z(ii+1,jj+1,kk+1,ll+1,
                                                             v.real,v.imag)+'\n')


def print_ao_bi(mf,kconserv=None,outfilename='W.ao.qp',bielec_int_threshold = 1E-8):

    cell = mf.cell
    kpts = mf.kpts
    nao = mf.cell.nao
    Nk = kpts.shape[0]

    if (kconserv is None):
        from pyscf.pbc.tools import get_kconserv
        kconserv = get_kconserv(cell, kpts)

    with open(outfilename,'w') as outfile:
        for d, kd in enumerate(kpts):
            for c, kc in enumerate(kpts):
                if c > d: break
                #idx2_cd = idx2_tri((c,d))
                for b, kb in enumerate(kpts):
                    if b > d: break
                    a = kconserv[b,c,d]
                    if a > d: continue
                    #if idx2_tri((a,b)) > idx2_cd: continue
                    #if ((c==d) and (a>b)): continue
                    ka = kpts[a]

                    eri_4d_ao_kpt = mf.with_df.get_ao_eri(kpts=[ka,kb,kc,kd],
                                                          compact=False).reshape((nao,)*4)
                    eri_4d_ao_kpt *= 1./Nk
                    for l in range(nao):
                        ll=l+d*nao
                        for j in range(nao):
                            jj=j+c*nao
                            if jj>ll: break
                            idx2_jjll = idx2_tri((jj,ll))
                            for k in range(nao):
                                kk=k+b*nao
                                if kk>ll: break
                                for i in range(nao):
                                    ii=i+a*nao
                                    if idx2_tri((ii,kk)) > idx2_jjll: break
                                    if ((jj==ll) and (ii>kk)): break
                                    v=eri_4d_ao_kpt[i,k,j,l]
                                    if (abs(v) > bielec_int_threshold):
                                        outfile.write(stri4z(ii+1,jj+1,kk+1,ll+1,
                                                             v.real,v.imag)+'\n')


def print_kcon_chem_to_phys(kcon,fname):
    '''
    input: kconserv in chem notation kcon_c[a,b,c] = d
           where (ab|cd) is allowed by symmetry
    output: kconserv in phys notation kcon_p[i,j,k] = l
            where <ij|kl> is allowed by symmetry
            (printed to file)
    '''
    Nk,n2,n3 = kcon.shape
    if (n2!=n3 or Nk!=n2):
        raise Exception('print_kcon_chem_to_phys called with non-cubic array')

    with open(fname,'w') as outfile:
        for a in range(Nk):
            for b in range(Nk):
                for c in range(Nk):
                    d = kcon[a,b,c]
                    outfile.write(stri4(a+1,c+1,b+1,d+1)+'\n')
    
def print_kpts_unblocked(ints_k,outfilename,thresh):
    '''
    for ints_k of shape (Nk,n1,n2),
    print the elements of the corresponding block-diagonal matrix of shape (Nk*n1,Nk*n2) in file
    '''
    Nk,n1,n2 = ints_k.shape
    with open(outfilename,'w') as outfile:
        for ik in range(Nk):
            shift1 = ik*n1+1
            shift2 = ik*n2+1
            for i1 in range(n1):
                for i2 in range(n2):
                    int_ij = ints_k[ik,i1,i2]
                    if abs(int_ij) > thresh:
                        outfile.write(stri2z(i1+shift1, i2+shift2, int_ij.real, int_ij.imag)+'\n')
    return

def print_kpts_unblocked_upper(ints_k,outfilename,thresh):
    '''
    for hermitian ints_k of shape (Nk,n1,n1),
    print the elements of the corresponding block-diagonal matrix of shape (Nk*n1,Nk*n1) in file
    (only upper triangle is printed)
    '''
    Nk,n1,n2 = ints_k.shape
    if (n1!=n2):
        raise Exception('print_kpts_unblocked_upper called with non-square matrix')

    with open(outfilename,'w') as outfile:
        for ik in range(Nk):
            shift = ik*n1+1
            for i1 in range(n1):
                for i2 in range(i1,n1):
                    int_ij = ints_k[ik,i1,i2]
                    if abs(int_ij) > thresh:
                        outfile.write(stri2z(i1+shift, i2+shift, int_ij.real, int_ij.imag)+'\n')
    return



def get_kin_ao(mf):
    nao = mf.cell.nao_nr()
    Nk = len(mf.kpts)
    return np.reshape(mf.cell.pbc_intor('int1e_kin',1,1,kpts=mf.kpts),(Nk,nao,nao))

def get_ovlp_ao(mf):
    nao = mf.cell.nao_nr()
    Nk = len(mf.kpts)
    return np.reshape(mf.get_ovlp(cell=mf.cell,kpts=mf.kpts),(Nk,nao,nao))

def get_pot_ao(mf):
    nao = mf.cell.nao_nr()
    Nk = len(mf.kpts)

    if mf.cell.pseudo:
        v_kpts_ao = np.reshape(mf.with_df.get_pp(kpts=mf.kpts),(Nk,nao,nao))
    else:
        v_kpts_ao = np.reshape(mf.with_df.get_nuc(kpts=mf.kpts),(Nk,nao,nao))

    if len(mf.cell._ecpbas) > 0:
        from pyscf.pbc.gto import ecp
        v_kpts_ao += np.reshape(ecp.ecp_int(mf.cell, mf.kpts),(Nk,nao,nao))

    return v_kpts_ao

def ao_to_mo_1e(ao_kpts,mo_coef):
    return np.einsum('kim,kij,kjn->kmn',mo_coef.conj(),ao_kpts_ao,mo_coef)

def get_j3ao_old(fname,nao,Nk):
    '''
    returns list of Nk_pair arrays of shape (naux,nao,nao)
    if naux is the same for each pair, returns numpy array
    if naux is not the same for each pair, returns array of arrays
    '''
    import h5py
    with h5py.File(fname,'r') as intfile:
        j3c = intfile.get('j3c')
        j3ckeys = list(j3c.keys())
        j3ckeys.sort(key=lambda strkey:int(strkey))
    
        # in new(?) version of PySCF, there is an extra layer of groups before the datasets
        # datasets used to be [/j3c/0,   /j3c/1,   /j3c/2,   ...]
        # datasets now are    [/j3c/0/0, /j3c/1/0, /j3c/2/0, ...]
        j3clist = [j3c.get(i+'/0') for i in j3ckeys]
        #if j3clist==[None]*len(j3clist):
        if not(any(j3clist)):
        # if using older version, stop before last level
            j3clist = [j3c.get(i) for i in j3ckeys]
    
        naosq = nao*nao
        naotri = (nao*(nao+1))//2
        nkinvsq = 1./np.sqrt(Nk)
    
        # dimensions are (kikj,iaux,jao,kao), where kikj is compound index of kpts i and j
        # output dimensions should be reversed (nao, nao, naux, nkptpairs)
        return np.array([(i.value.reshape([-1,nao,nao]) if (i.shape[1] == naosq) else makesq3(i.value,nao)) * nkinvsq for i in j3clist])

def get_j3ao(fname,nao,Nk):
    '''
    returns padded df AO array
    fills in zeros when functions are dropped due to linear dependency
    last AO index corresponds to smallest kpt index?
    (k, mu, i, j) where i.kpt >= j.kpt
    '''
    import h5py
    with h5py.File(fname,'r') as intfile:
        j3c = intfile.get('j3c')
        j3ckeys = list(j3c.keys())
        nkpairs = len(j3ckeys)

        # get num order instead of lex order
        j3ckeys.sort(key=lambda strkey:int(strkey))

        # in new(?) version of PySCF, there is an extra layer of groups before the datasets
        # datasets used to be [/j3c/0,   /j3c/1,   /j3c/2,   ...]
        # datasets now are    [/j3c/0/0, /j3c/1/0, /j3c/2/0, ...]
        keysub = '/0' if bool(j3c.get('0/0',getclass=True)) else ''

        naux = max(map(lambda k: j3c[k+keysub].shape[0],j3c.keys()))

        naosq = nao*nao
        naotri = (nao*(nao+1))//2
        nkinvsq = 1./np.sqrt(Nk)

        j3arr = np.zeros((nkpairs,naux,nao,nao),dtype=np.complex128)

        for i,kpair in enumerate(j3ckeys):
            iaux,dim2 = j3c[kpair+keysub].shape
            if (dim2==naosq):
                j3arr[i,:iaux,:,:] = j3c[kpair+keysub][()].reshape([iaux,nao,nao]) * nkinvsq
                #j3arr[i,:iaux,:,:] = j3c[kpair+keysub][()].reshape([iaux,nao,nao]).transpose((0,2,1)) * nkinvsq
            else:
                j3arr[i,:iaux,:,:] = makesq3(j3c[kpair+keysub][()],nao) * nkinvsq
                #j3arr[i,:iaux,:,:] = makesq3(j3c[kpair+keysub][()].conj(),nao) * nkinvsq

        return j3arr

def get_j3ao_new(fname,nao,Nk):
    '''
    returns padded df AO array
    fills in zeros when functions are dropped due to linear dependency
    last AO index corresponds to largest kpt index?
    (k, mu, j, i) where i.kpt >= j.kpt
    '''
    import h5py
    with h5py.File(fname,'r') as intfile:
        j3c = intfile.get('j3c')
        j3ckeys = list(j3c.keys())
        nkpairs = len(j3ckeys)

        # get num order instead of lex order
        j3ckeys.sort(key=lambda strkey:int(strkey))

        # in new(?) version of PySCF, there is an extra layer of groups before the datasets
        # datasets used to be [/j3c/0,   /j3c/1,   /j3c/2,   ...]
        # datasets now are    [/j3c/0/0, /j3c/1/0, /j3c/2/0, ...]
        keysub = '/0' if bool(j3c.get('0/0',getclass=True)) else ''

        naux = max(map(lambda k: j3c[k+keysub].shape[0],j3c.keys()))

        naosq = nao*nao
        naotri = (nao*(nao+1))//2
        nkinvsq = 1./np.sqrt(Nk)

        j3arr = np.zeros((nkpairs,naux,nao,nao),dtype=np.complex128)

        for i,kpair in enumerate(j3ckeys):
            iaux,dim2 = j3c[kpair+keysub].shape
            if (dim2==naosq):
                j3arr[i,:iaux,:,:] = j3c[kpair+keysub][()].reshape([iaux,nao,nao]).transpose((0,2,1)) * nkinvsq
            else:
                j3arr[i,:iaux,:,:] = makesq3(j3c[kpair+keysub][()].conj(),nao) * nkinvsq

        return j3arr

def print_df(j3arr,fname,thresh):
    with open(fname,'w') as outfile:
        for k,kpt_pair in enumerate(j3arr):
            for iaux,dfbasfunc in enumerate(kpt_pair):
                for i,i0 in enumerate(dfbasfunc):
                    for j,v in enumerate(i0):
                        if (abs(v) > thresh):
                            outfile.write(stri4z(i+1,j+1,iaux+1,k+1,v.real,v.imag)+'\n')
    return

def df_pad_ref_test(j3arr,nao,naux,nkpt_pairs):
    df_ao_tmp = np.zeros((nao,nao,naux,nkpt_pairs),dtype=np.complex128)
    for k,kpt_pair in enumerate(j3arr):
        for iaux,dfbasfunc in enumerate(kpt_pair):
            for i,i0 in enumerate(dfbasfunc):
                for j,v in enumerate(i0):
                    df_ao_tmp[i,j,iaux,k]=v
    return df_ao_tmp


def df_ao_to_mo(j3ao,mo_coef):
    from itertools import product
    Nk = mo_coef.shape[0]
    kpair_list = ((i,j,idx2_tri((i,j))) for (i,j) in product(range(Nk),repeat=2) if (i>=j))
    return np.array([
        np.einsum('mij,ik,jl->mkl',j3ao[kij],mo_coef[ki].conj(),mo_coef[kj])
        for ki,kj,kij in kpair_list])

    
def df_ao_to_mo_new(j3ao,mo_coef):
    #TODO: fix this (C/F ordering, conj, transpose, view cmplx->float)

    from itertools import product
    Nk = mo_coef.shape[0]
    return np.array([
        np.einsum('mji,ik,jl->mlk',j3ao[idx2_tri((ki,kj))],mo_coef[ki].conj(),mo_coef[kj])
        for ki,kj in product(range(Nk),repeat=2) if (ki>=kj)])

def df_ao_to_mo_test(j3ao,mo_coef):
    from itertools import product
    Nk = mo_coef.shape[0]
    return np.array([
        np.einsum('mij,ik,jl->mkl',j3ao[idx2_tri((ki,kj))],mo_coef[ki].conj(),mo_coef[kj])
        for ki,kj in product(range(Nk),repeat=2) if (ki>=kj)])


def pyscf2QP2(cell,mf, kpts, kmesh=None, cas_idx=None, int_threshold = 1E-8, 
        print_ao_ints_bi=False, 
        print_mo_ints_bi=False, 
        print_ao_ints_df=True, 
        print_mo_ints_df=False, 
        print_ao_ints_mono=True, 
        print_mo_ints_mono=False):
    '''
    kpts = List of kpoints coordinates. Cannot be null, for gamma is other script
    kmesh = Mesh of kpoints (optional)
    cas_idx = List of active MOs. If not specified all MOs are actives
    int_threshold = The integral will be not printed in they are bellow that
    '''
  
#    from pyscf.pbc import ao2mo
    from pyscf.pbc import tools
    import h5py
#    import scipy
    from scipy.linalg import block_diag

    mo_coef_threshold = int_threshold
    ovlp_threshold = int_threshold
    kin_threshold = int_threshold
    ne_threshold = int_threshold
    bielec_int_threshold = int_threshold
    thresh_mono = int_threshold
    
    
    qph5path = 'qpdat.h5'
    # create hdf5 file, delete old data if exists
    with h5py.File(qph5path,'w') as qph5:
        qph5.create_group('nuclei')
        qph5.create_group('electrons')
        qph5.create_group('ao_basis')
        qph5.create_group('mo_basis')

    mo_coeff = mf.mo_coeff
    # Mo_coeff actif
    mo_k = np.array([c[:,cas_idx] for c in mo_coeff] if cas_idx is not None else mo_coeff)
    e_k =  np.array([e[cas_idx] for e in mf.mo_energy] if cas_idx is not None else mf.mo_energy)
  
    Nk, nao, nmo = mo_k.shape

    print("n Kpts", Nk)
    print("n active Mos per kpt", nmo)
    print("n AOs per kpt", nao)

    ##########################################
    #                                        #
    #                Nuclei                  #
    #                                        #
    ##########################################

    natom = cell.natm
    print('n_atom per kpt',   natom)

    atom_xyz = mf.cell.atom_coords()
    if not(mf.cell.unit.startswith(('B','b','au','AU'))):
        from pyscf.data.nist import BOHR
        atom_xyz /= BOHR # always convert to au

    with h5py.File(qph5path,'a') as qph5:
        qph5['nuclei'].attrs['kpt_num']=Nk
        qph5['nuclei'].attrs['nucl_num']=natom
        qph5.create_dataset('nuclei/nucl_coord',data=atom_xyz)
        qph5.create_dataset('nuclei/nucl_charge',data=mf.cell.atom_charges())

        strtype=h5py.special_dtype(vlen=str)
        atom_dset=qph5.create_dataset('nuclei/nucl_label',(natom,),dtype=strtype)
        for i in range(natom):
            atom_dset[i] = mf.cell.atom_pure_symbol(i)

    ##########################################
    #                                        #
    #                Basis                   #
    #                                        #
    ##########################################

    # nucleus on which each AO is centered
    ao_nucl=[i[0] for i in mf.cell.ao_labels(fmt=False,base=1)]

    with h5py.File(qph5path,'a') as qph5:
        qph5['mo_basis'].attrs['mo_num']=Nk*nmo
        qph5['ao_basis'].attrs['ao_num']=Nk*nao

        qph5['ao_basis'].attrs['ao_basis']=mf.cell.basis

        qph5.create_dataset('ao_basis/ao_nucl',data=Nk*ao_nucl)

    ##########################################
    #                                        #
    #              Electrons                 #
    #                                        #
    ##########################################

    nelec = cell.nelectron
    neleca,nelecb = cell.nelec

    print('num_elec per kpt', nelec)

    with h5py.File(qph5path,'a') as qph5:
        #in old version: param << nelec*Nk, nmo*Nk, natom*Nk
        qph5['electrons'].attrs['elec_alpha_num']=neleca*Nk 
        qph5['electrons'].attrs['elec_beta_num']=nelecb*Nk

    ##########################################
    #                                        #
    #           Nuclear Repulsion            #
    #                                        #
    ##########################################

    #Total energy shift due to Ewald probe charge = -1/2 * Nelec*madelung/cell.vol =
    shift = tools.pbc.madelung(cell, kpts)*cell.nelectron * -.5 
    e_nuc = (cell.energy_nuc() + shift)*Nk
  
    print('nucl_repul', e_nuc)

    with h5py.File(qph5path,'a') as qph5:
        qph5['nuclei'].attrs['nuclear_repulsion']=e_nuc
  
    ##########################################
    #                                        #
    #               MO Coef                  #
    #                                        #
    ##########################################
    
    with h5py.File(qph5path,'a') as qph5:
        # k,mo,ao(,2)
        mo_coef_f = np.array(mo_k.transpose((0,2,1)),order='c')
        mo_coef_blocked=block_diag(*mo_k)
        mo_coef_blocked_f = block_diag(*mo_coef_f)
        qph5.create_dataset('mo_basis/mo_coef_real',data=mo_coef_blocked.real)
        qph5.create_dataset('mo_basis/mo_coef_imag',data=mo_coef_blocked.imag)
        qph5.create_dataset('mo_basis/mo_coef_kpts_real',data=mo_k.real)
        qph5.create_dataset('mo_basis/mo_coef_kpts_imag',data=mo_k.imag)
        qph5.create_dataset('mo_basis/mo_coef_complex',data=mo_coef_blocked_f.view(dtype=np.float64).reshape((Nk*nmo,Nk*nao,2)))
        qph5.create_dataset('mo_basis/mo_coef_complex_kpts',data=mo_coef_f.view(dtype=np.float64).reshape((Nk,nmo,nao,2)))
   
    print_kpts_unblocked(mo_k,'C.qp',mo_coef_threshold)   

    ##########################################
    #                                        #
    #            Integrals Mono              #
    #                                        #
    ##########################################
    
    ne_ao = get_pot_ao(mf)
    kin_ao = get_kin_ao(mf)
    ovlp_ao = get_ovlp_ao(mf)

    if print_ao_ints_mono:

        with h5py.File(qph5path,'a') as qph5:
            kin_ao_blocked=block_diag(*kin_ao)
            ovlp_ao_blocked=block_diag(*ovlp_ao)
            ne_ao_blocked=block_diag(*ne_ao)

            kin_ao_f =  np.array(kin_ao.transpose((0,2,1)),order='c')
            ovlp_ao_f = np.array(ovlp_ao.transpose((0,2,1)),order='c')
            ne_ao_f =   np.array(ne_ao.transpose((0,2,1)),order='c')

            kin_ao_blocked_f = block_diag(*kin_ao_f)
            ovlp_ao_blocked_f = block_diag(*ovlp_ao_f)
            ne_ao_blocked_f = block_diag(*ne_ao_f)

            qph5.create_dataset('ao_one_e_ints/ao_integrals_kinetic_real',data=kin_ao_blocked.real)
            qph5.create_dataset('ao_one_e_ints/ao_integrals_kinetic_imag',data=kin_ao_blocked.imag)
            qph5.create_dataset('ao_one_e_ints/ao_integrals_overlap_real',data=ovlp_ao_blocked.real)
            qph5.create_dataset('ao_one_e_ints/ao_integrals_overlap_imag',data=ovlp_ao_blocked.imag)
            qph5.create_dataset('ao_one_e_ints/ao_integrals_n_e_real',    data=ne_ao_blocked.real)
            qph5.create_dataset('ao_one_e_ints/ao_integrals_n_e_imag',    data=ne_ao_blocked.imag)

            qph5.create_dataset('ao_one_e_ints/ao_integrals_kinetic',data=kin_ao_blocked_f.view(dtype=np.float64).reshape((Nk*nao,Nk*nao,2)))
            qph5.create_dataset('ao_one_e_ints/ao_integrals_overlap',data=ovlp_ao_blocked_f.view(dtype=np.float64).reshape((Nk*nao,Nk*nao,2)))
            qph5.create_dataset('ao_one_e_ints/ao_integrals_n_e',    data=ne_ao_blocked_f.view(dtype=np.float64).reshape((Nk*nao,Nk*nao,2)))

        for fname,ints in zip(('S.qp','V.qp','T.qp'),
                              (ovlp_ao, ne_ao, kin_ao)):
            print_kpts_unblocked_upper(ints,fname,thresh_mono)

    if print_mo_ints_mono:
        kin_mo = ao_to_mo_1e(kin_ao,mo_k)
        ovlp_mo = ao_to_mo_1e(ovlp_ao,mo_k)
        ne_mo = ao_to_mo_1e(ne_ao,mo_k)

        kin_mo_blocked=block_diag(*kin_mo)
        ovlp_mo_blocked=block_diag(*ovlp_mo)
        ne_mo_blocked=block_diag(*ne_mo)

        with h5py.File(qph5path,'a') as qph5:
            qph5.create_dataset('mo_one_e_ints/mo_integrals_kinetic_real',data=kin_mo_blocked.real)
            qph5.create_dataset('mo_one_e_ints/mo_integrals_kinetic_imag',data=kin_mo_blocked.imag)
            qph5.create_dataset('mo_one_e_ints/mo_integrals_overlap_real',data=ovlp_mo_blocked.real)
            qph5.create_dataset('mo_one_e_ints/mo_integrals_overlap_imag',data=ovlp_mo_blocked.imag)
            qph5.create_dataset('mo_one_e_ints/mo_integrals_n_e_real',    data=ne_mo_blocked.real)
            qph5.create_dataset('mo_one_e_ints/mo_integrals_n_e_imag',    data=ne_mo_blocked.imag)
        for fname,ints in zip(('S.mo.qp','V.mo.qp','T.mo.qp'),
                              (ovlp_mo, ne_mo, kin_mo)):
            print_kpts_unblocked_upper(ints,fname,thresh_mono)

  
    ##########################################
    #                                        #
    #               k-points                 #
    #                                        #
    ##########################################

    kconserv = tools.get_kconserv(cell, kpts)

    with h5py.File(qph5path,'a') as qph5:
        kcon_f_phys = np.array(kconserv.transpose((1,2,0)),order='c')
        qph5.create_dataset('nuclei/kconserv',data=kcon_f_phys+1)

    print_kcon_chem_to_phys(kconserv,'K.qp')
  
    ##########################################
    #                                        #
    #             Integrals Bi               #
    #                                        #
    ##########################################

    j3arr = get_j3ao(mf.with_df._cderi,nao,Nk)

    # test? nkpt_pairs should be (Nk*(Nk+1))//2
    nkpt_pairs, naux, _, _ = j3arr.shape

    print("n df fitting functions", naux)
    with h5py.File(qph5path,'a') as qph5:
        qph5.create_group('ao_two_e_ints')
        qph5['ao_two_e_ints'].attrs['df_num']=naux

    if print_ao_ints_df:
        print_df(j3arr,'D.qp',bielec_int_threshold)
        j3ao_new = get_j3ao_new(mf.with_df._cderi,nao,Nk)

        with h5py.File(qph5path,'a') as qph5:
            #qph5.create_dataset('ao_two_e_ints/df_ao_integrals_real',data=j3arr.transpose((2,3,1,0)).real)
            #qph5.create_dataset('ao_two_e_ints/df_ao_integrals_imag',data=j3arr.transpose((2,3,1,0)).imag)
            qph5.create_dataset('ao_two_e_ints/df_ao_integrals',data=j3ao_new.view(dtype=np.float64).reshape((nkpt_pairs,naux,nao,nao,2)))

    if print_mo_ints_df:

        j3mo = df_ao_to_mo(j3arr,mo_k)
        j3mo_new = df_ao_to_mo_new(j3ao_new,mo_k)

        print_df(j3mo,'D.mo.qp',bielec_int_threshold)

        with h5py.File(qph5path,'a') as qph5:
            #qph5.create_dataset('mo_two_e_ints/df_mo_integrals_real',data=j3mo.transpose((2,3,1,0)).real)
            #qph5.create_dataset('mo_two_e_ints/df_mo_integrals_imag',data=j3mo.transpose((2,3,1,0)).imag)
            qph5.create_dataset('mo_two_e_ints/df_mo_integrals',data=j3mo_new.view(dtype=np.float64).reshape((nkpt_pairs,naux,nmo,nmo,2)))

    if (print_ao_ints_bi):
        print_ao_bi(mf,kconserv,'W.qp',bielec_int_threshold)
    if (print_mo_ints_bi):
        print_mo_bi(mf,kconserv,'W.mo.qp',cas_idx,bielec_int_threshold)
    return