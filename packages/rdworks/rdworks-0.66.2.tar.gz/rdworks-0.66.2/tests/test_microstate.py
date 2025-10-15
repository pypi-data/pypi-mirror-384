from re import A
import numpy as np
import math
import pytest
import pathlib
import tempfile
from dataclasses import asdict
from rdworks import State, StateEnsemble, StateNetwork


@pytest.fixture(scope='module') # Runs once for every test module (file).
def prepared_state():
    smiles = 'c1ccc(CNc2ncnc3ccccc23)cc1'
    st = State(smiles=smiles)
    return st


def test_state_serialize(prepared_state):
    st = prepared_state
    serialized = st.serialize()
    st2 = State().deserialize(serialized)
    assert st.smiles == st2.smiles
    assert len(st.sites) == len(st2.sites)
    assert st.origin == st2.origin
    assert st.transformation == st2.transformation
    assert st.tautomer_rule == st2.tautomer_rule
    assert st.charge == st2.charge


def test_site(prepared_state):
    """Ionizable site"""
    st = prepared_state
    assert st.site_info() == [
        ('N', 5, 0, True, True),
        ('N', 7, 0, True, False), 
        ('N', 9, 0, True, False), 
        ]
    # SMILES: c1ccc(CNc2ncnc3ccccc23)cc1
    # Formal charge: 0
    # Origin: None
    # Transformation: None
    # Ionizable sites:
    # - atom_idx=  5, atom=  N, q= +0, hs= 1, pr= 1, de= 1, acid_base= B:A:A, name= Amine:Amide:Amide vinylogue
    # - atom_idx=  7, atom=  N, q= +0, hs= 0, pr= 1, de= 0, acid_base= B, name= Aza-aromatics
    # - atom_idx=  9, atom=  N, q= +0, hs= 0, pr= 1, de= 0, acid_base= B, name= Aza-aromatics
    
    smiles = 'C1=Nc2ccccc2C(N=Cc2ccccc2)N1'
    st = State(smiles=smiles)
    assert st.site_info() == [
        ('N', 1, 0, True, False), 
        ('N', 9, 0, True, False), 
        ('N', 17, 0, True, True)]
    # SMILES: C1=Nc2ccccc2C(N=Cc2ccccc2)N1
    # Formal charge: 0
    # Origin: None
    # Transformation: None
    # Ionizable sites:
    # - atom_idx=  1, atom=  N, q= +0, hs= 0, pr= 1, de= 0, acid_base= B, name= Imine
    # - atom_idx=  9, atom=  N, q= +0, hs= 0, pr= 1, de= 0, acid_base= B, name= Imine
    # - atom_idx= 17, atom=  N, q= +0, hs= 1, pr= 1, de= 1, acid_base= A, name= Amide


def test_tautomers():
    smiles = 'c1ccc(CNc2ncnc3ccccc23)cc1'
    st1 = State(smiles=smiles, tautomer_rule='rdkit')
    se1 = StateEnsemble(st1.get_tautomers())
    assert se1.size() == 2
    st2 = State(smiles=smiles, tautomer_rule='comprehensive')
    se2 = StateEnsemble(st2.get_tautomers()) 
    assert se2.size() == 20


def test_protonate(prepared_state):
    st = prepared_state
    ps = st.get_protonated(atom_idx=9)
    assert len(ps) == 1
    assert ps[0].site_info() == [
        ('N', 5, 0, True, True),
        ('N', 7, 0, True, False), 
        ('N', 9, 1, False, True),
        ]
    # SMILES: c1ccc(CNc2nc[nH+]c3ccccc23)cc1
    # Formal charge: 1
    # Origin: c1ccc(CNc2ncnc3ccccc23)cc1
    # Transformation: +H
    # Ionizable sites:
    # - atom_idx=  5, atom=  N, q= +0, hs= 1, pr= 1, de= 1, acid_base= B:A:A, name= Amine:Amide:Amide vinylogue
    # - atom_idx=  7, atom=  N, q= +0, hs= 0, pr= 1, de= 0, acid_base= B, name= Aza-aromatics
    # - atom_idx=  9, atom=  N, q= +1, hs= 1, pr= 0, de= 1, acid_base= A, name= Aza-aromatics

    ps = st.get_protonated(site_idx=2)
    assert len(ps) == 1
    assert ps[0].site_info() == [
        ('N', 5, 0, True, True),
        ('N', 7, 0, True, False), 
        ('N', 9, 1, False, True),
        ]

    se = StateEnsemble(st.get_protonated())
    assert se.size() == 3
    results = [_.smiles for _ in se]
    expected = ['c1ccc(C[NH2+]c2ncnc3ccccc23)cc1',
                'c1ccc(CNc2[nH+]cnc3ccccc23)cc1',
                'c1ccc(CNc2nc[nH+]c3ccccc23)cc1'
                ]
    assert set(results) == set(expected)


def test_deprotonate(prepared_state):
    st = prepared_state
    des = st.get_deprotonated(atom_idx=5)
    assert len(des) == 1
    assert des[0].site_info() == [
        ('N', 5, -1, True, False),
        ('N', 7, 0, True, False), 
        ('N', 9, 0, True, False),
    ]

    des = st.get_deprotonated(site_idx=0)
    assert len(des) == 1
    assert des[0].site_info() == [
        ('N', 5, -1, True, False),
        ('N', 7, 0, True, False), 
        ('N', 9, 0, True, False),
    ]

    des = st.get_deprotonated(atom_idx=7)
    assert len(des) == 0

    se = StateEnsemble(st.get_deprotonated())
    assert se.size() == 1
    results = [_.smiles for _ in se]
    expected = ['c1ccc(C[N-]c2ncnc3ccccc23)cc1']
    assert set(results) == set(expected)


# def test_sn():
#     smiles = 'c1ccc(CNc2ncnc3ccccc23)cc1'
#     sn1 = StateNetwork()
#     sn1.build(smiles=smiles, tautomer_rule=None)
#     assert len(sn1.visited_states) == 11
#     assert len(sn1.graph.nodes()) == 11
#     sn2 = StateNetwork()
#     sn2.build(smiles=smiles, tautomer_rule='rdkit')
#     assert len(sn2.visited_states) == 33
#     assert len(sn2.graph.nodes()) == 33
#     sn3 = StateNetwork()
#     sn3.build(smiles=smiles, tautomer_rule='comprehensive')
#     assert len(sn3.visited_states) == 183
#     assert len(sn3.graph.nodes()) == 183
    

def test_unipka_workflow():
    smiles = 'c1ccc(CNc2ncnc3ccccc23)cc1'
    sn = StateNetwork()
    sn.build(smiles=smiles, max_formal_charge=3, tautomer_rule=None)
    assert len(sn.visited_states) == 12
    assert len(sn.graph.nodes()) == 12

    serialized = sn.serialize()
    sn2 = StateNetwork().deserialize(serialized)
    assert sn2.size() ==sn.size()
    assert sn2.get_num_nodes() == sn.get_num_nodes()
    assert sn2.get_num_edges() == sn.get_num_edges()
    assert sn2.get_initial_state() == sn.get_initial_state()
    assert sn2.get_state_ensemble() == sn.get_state_ensemble()
    
    sn.info()
    sn.get_initial_state().info()
    sn.get_state_ensemble().info()

    assert sn.get_num_nodes() == sn.get_state_ensemble().size()

    # calculated from Uni-pKa
    LN10 = math.log(10)
    TRANSLATE_PH = 6.504894871171601
    # Uni-pka model specific variable for pH dependent deltaG
    # Training might be conducted with a dataset in which raw pKa values
    # were subtracted by the mean value (TRANSLATE_PH).
    FE = np.array([-6.025253772735596, -2.9201512336730957, -2.7405877113342285, 
          -2.9639060497283936, 7.656927108764648, 19.67357063293457, 
          21.269811630249023, 11.911577224731445, 7.5623698234558105, 
          10.144123077392578, 21.36874008178711, 12.132856369018555])
    
    sn.set_energies(FE)
    se = sn.get_state_ensemble()

    se2 = StateEnsemble([st for st in sn.get_state_ensemble()])
    assert se.size() == se2.size()
    assert se == se2
    assert all(math.isclose(x, y) for x, y in zip([st.energy for st in se], [st.energy for st in se2]))

    # micro-pKa
    micro = se.get_micro_pKa(beta=1.0)
    micro_pKa = {}
    for k, v in micro.items():
        # translation is necessary!!
        micro_pKa[k] = (np.array(v)/LN10 + TRANSLATE_PH).tolist()
    expected_micro_pKa = {
        5: [5.263056256779453, 12.37074708270436], 
        7: [5.190629233663213], 
        9: [5.280577863433882],
        }
    assert micro_pKa.keys() == expected_micro_pKa.keys()
    for k,v in micro_pKa.items():
        for x, y in zip(v, expected_micro_pKa[k]):
            assert math.isclose(x, y)

    # macro-pKa
    macro = se.get_macro_pKa(beta=1.0)
    expected_macro_pKa = [5.248700101444452, 12.3693201962264]
    macro_pKa = (np.array(macro)/LN10 + TRANSLATE_PH).tolist()
    for x, y in zip(macro_pKa, expected_macro_pKa):
        assert math.isclose(x, y)

    # population
    pH = np.array([1.2, 7.4, 14.0]) - TRANSLATE_PH
    p = sn.get_population(pH, C=LN10, beta=1.0)
    expected_p = [
        [2.6935020358203173e-05, 0.983819163640424, 0.027227135908720494], 
        [0.24360336373466238, 0.005614114302596941, 3.9027248338257366e-11], 
        [0.20356346464419176, 0.0046913496629296765, 3.2612529504798934e-11], 
        [0.25449881002178604, 0.005865212152380097, 4.077278781474373e-11], 
        [1.5251999407276225e-16, 8.829269017020774e-06, 0.9727728271965177], 
        [7.57267676610138e-06, 1.1011522978789083e-13, 1.9227998109993388e-28], 
        [1.534655014453089e-06, 2.2315608440876436e-14, 3.89668602382293e-29], 
        [0.01779263728460303, 2.5872494015551734e-10, 4.517778939299372e-25], 
        [3.382885964170599e-11, 1.2356211340110039e-06, 3.419574022416676e-08], 
        [2.5588578837852876e-12, 9.346395100583787e-08, 2.5866091967405752e-09], 
        [0.2805056112545945, 2.5735909639257094e-15, 1.1288239220348465e-36], 
        [7.067163565804634e-08, 1.6287075615586162e-09, 1.1322173195857867e-17]
        ]
   
    for x, y in zip(p, expected_p):
        for xz, yz in zip(x, y):
            assert math.isclose(xz, yz, abs_tol=1e-6)

    print("\n")
    for k, st in enumerate(sn.visited_states):
        print(f"{k:2} {st.smiles:50} {FE[k]:8.3f} {p[k]}")

    # population chart
    pH = np.linspace(0, 14, 60)
    p = sn.get_population(pH=pH-TRANSLATE_PH, C=LN10, beta=1.0)

    chart, populated_state_idx = sn.get_pH_population_chart(
                                        pH=pH-TRANSLATE_PH, 
                                        ignore_below=0.05,
                                        pH_label=pH, 
                                        C=LN10, 
                                        beta=1.0,
                                        width=600,
                                        height=400)
    
    print(f"Number of populated states: {len(populated_state_idx)}")
    print(f"Populated states (index in the state ensemble): {populated_state_idx}")
    
    with tempfile.TemporaryDirectory() as temp_dir: # tmpdir is a string
        workdir = pathlib.Path(__file__).parent.resolve() / "outfiles"
        # workdir = pathlib.Path(temp_dir)
        with open(workdir / 'microstate_population_plot.html', 'w') as f:
            chart_json = chart.to_json()
            html = f"""<!DOCTYPE html>
    <html>
        <head>
            <title>Altair Chart</title>
            <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
            <script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
            <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
        </head>
        <body>
            <div id="chart-container"></div>
            <script type="text/javascript">
                var spec = JSON.parse(`{chart_json}`);
                vegaEmbed('#chart-container', spec).then(
                    result => console.log(result)).catch(console.warn);
            </script>
        </body>
    </html>"""
            f.write(html)


def test_trim():
    LN10 = math.log(10)
    TRANSLATE_PH = 6.504894871171601

    smiles = 'c1ccc(CNc2ncnc3ccccc23)cc1'
    sn = StateNetwork()
    sn.build(smiles=smiles, max_formal_charge=3, tautomer_rule=None)
    FE = np.array([-6.025253772735596, -2.9201512336730957, -2.7405877113342285, 
          -2.9639060497283936, 7.656927108764648, 19.67357063293457, 
          21.269811630249023, 11.911577224731445, 7.5623698234558105, 
          10.144123077392578, 21.36874008178711, 12.132856369018555])
    sn.set_energies(FE)

    se = sn.get_state_ensemble()

    pH = np.linspace(0.0, 14.0, 60) -  TRANSLATE_PH
    sn0 = sn.copy()
    sn.trim(pH, threshold=0.05)
    print(f'{len(sn0.visited_states)} --> {len(sn.visited_states)}')

    se0 = se.copy()
    se.trim(pH, threshold=0.05)
    print(f'{se0.size()} --> {se.size()}')