from rdworks import Mol
from rdworks.utils import recursive_round


def test_align_and_cluster_confs():
    mol = Mol("N=C1O[C@@H](CN1)CN2C[C@H](O[C@H](C2)C)C", "stereoisomer")
    mol = mol.make_confs()
    mol = mol.drop_confs(similar=True, similar_rmsd=0.5, window=15.0)
    mol = mol.sort_confs().align_confs().cluster_confs().rename()
    mol.to_sdf(confs=True) # string output

def test_make_confs():
    mol = Mol("N=C1O[C@@H](CN1)CN2C[C@H](O[C@H](C2)C)C", "stereoisomer")
    mol = mol.make_confs(method='ETKDG')
    assert mol.num_confs > 1
    mol = mol.make_confs(method='CONFORGE')
    assert mol.num_confs > 1


def test_singlepoint():
    mol = Mol("N=C1O[C@@H](CN1)CN2C[C@H](O[C@H](C2)C)C", "stereoisomer")
    mol = mol.make_confs(n=10, method='ETKDG')
    mol = mol.singlepoint_confs(calculator='MMFF94')
    assert all([_.props.get('E_tot(kcal/mol)') is not None for _ in mol.confs])


def test_optimize_confs():
    mol = Mol("N=C1O[C@@H](CN1)CN2C[C@H](O[C@H](C2)C)C", "stereoisomer")
    mol = mol.make_confs().optimize_confs(calculator='MMFF94')


def test_workflow():
    state_mol = Mol('Cc1nc2cc(Cl)nc(Cl)c2nc1C', 'A-1250')
    state_mol = state_mol.make_confs(n=50, method='ETKDG')
    state_mol = state_mol.drop_confs(similar=True, similar_rmsd=0.3)
    state_mol = state_mol.sort_confs().rename()
    state_mol = state_mol.align_confs(method='rigid_fragment')
    state_mol = state_mol.cluster_confs('QT', threshold=1.0, sort='energy')
    print(state_mol.name, {k:v for k,v in state_mol.props.items()})
    for conf in state_mol.confs:
        conf.props = recursive_round(conf.props, decimals=2)
        print(conf.name, {k:v for k,v in conf.props.items()})


def test_protonate_deprotonate():
    mol = Mol('c1ccc(CNc2ncnc3ccccc23)cc1') # SAMPL6 SM07
    mol = mol.make_confs(n=1)
    # SMILES: c1ccc(CNc2ncnc3ccccc23)cc1
    # Formal charge: 0
    # Origin: None
    # Transformation: None
    # Ionizable sites:
    # - atom_idx=  5, atom=  N, q= +0, hs= 1, pr= 1, de= 1, acid_base= B:A:A, name= Amine:Amide:Amide vinylogue
    # - atom_idx=  7, atom=  N, q= +0, hs= 0, pr= 1, de= 0, acid_base= B, name= Aza-aromatics
    # - atom_idx=  9, atom=  N, q= +0, hs= 0, pr= 1, de= 0, acid_base= B, name= Aza-aromatics

    conf = mol.confs[0].copy()
    assert conf.positions.shape == (31, 3)
    assert conf.charge == 0
    
    conf = conf.protonate([7])
    assert conf.positions.shape == (32, 3)
    assert conf.charge == 1
    
    conf = mol.confs[0].copy()
    conf = conf.protonate([7,9])
    assert conf.positions.shape == (33, 3)
    assert conf.charge == 2
    
    conf = mol.confs[0].copy()
    conf = conf.deprotonate([5])
    assert conf.positions.shape == (30, 3)
    assert conf.charge == -1


def test_from_molblock():
    mol = Mol('c1ccc(CNc2ncnc3ccccc23)cc1') # SAMPL6 SM07
    mol = mol.make_confs(n=1)
    conf = mol.confs[0].copy()
    mol2 = Mol().from_molblock(conf.molblock)


def test_serialization():
    smiles = 'CC(C)C1=C(C(=C(N1CC[C@H](C[C@H](CC(=O)O)O)O)C2=CC=C(C=C2)F)C3=CC=CC=C3)C(=O)NC4=CC=CC=C4'
    name = 'atorvastatin'
    mol = Mol(smiles, name)
    assert mol.num_confs == 0
    assert mol.name == name
    mol = mol.make_confs(n=10)
    assert mol.num_confs == 10
    serialized = mol.serialize()
    rebuilt = Mol().deserialize(serialized)
    assert rebuilt.num_confs == 10
    assert rebuilt.name == name
    assert rebuilt == mol
    print(mol.confs[0].positions.shape)