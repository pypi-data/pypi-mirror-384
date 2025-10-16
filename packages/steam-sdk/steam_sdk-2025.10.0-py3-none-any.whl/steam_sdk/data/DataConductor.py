from pydantic import BaseModel, Field
from typing import Union, Literal, Optional, List

# This dataclass is used both by DataModelConductor and DataModelMagnet

class Ic_A_NbTi(BaseModel):
    """
    Level 3: Class for setting IcNbTi fit
    """
    type: Literal["Ic_A_NbTi"]
    Jc_5T_4_2K: Optional[float] = None  # [A/m^2]

class ConstantJc(BaseModel):
    """
        Level 3: Class for setting constant Jc
    """
    type: Literal['Constant Jc']
    Jc_constant: Optional[float] = None  # [A/m^2]


class Bottura(BaseModel):
    """
        Level 3: Class for setting Bottura fit
    """
    type: Literal['Bottura']
    Tc0_Bottura: Optional[float] = None  # [K]
    Bc20_Bottura: Optional[float] = None  # [T]
    Jc_ref_Bottura: Optional[float] = None  # [A/m^2]
    C0_Bottura: Optional[float] = None  # [-]
    alpha_Bottura: Optional[float] = None  # [-]
    beta_Bottura: Optional[float] = None  # [-]
    gamma_Bottura: Optional[float] = None  # [-]


class CUDI1(BaseModel):
    """
        Level 3: Class for Nb-Ti fit based on "Fit 1" in CUDI manual
    """
    type: Literal['CUDI1']
    Tc0_CUDI1: Optional[float] = None  # [K]
    Bc20_CUDI1: Optional[float] = None  # [T]
    C1_CUDI1: Optional[float] = None  # [A]
    C2_CUDI1: Optional[float] = None  # [A/T]


class CUDI3(BaseModel):
    """
        Level 3: Class for Nb-Ti fit based on "Fit 3" in CUDI manual
    """
    type: Literal['CUDI3']
    Tc0_CUDI3: Optional[float] = None  # [K]
    Bc20_CUDI3: Optional[float] = None  # [T]
    c1_CUDI3: Optional[float] = None  # [-]
    c2_CUDI3: Optional[float] = None  # [-]
    c3_CUDI3: Optional[float] = None  # [-]
    c4_CUDI3: Optional[float] = None  # [-]
    c5_CUDI3: Optional[float] = None  # [-]
    c6_CUDI3: Optional[float] = None  # [-]


class Summers(BaseModel):
    """
        Level 3: Class for cable Summer's Nb3Sn fit
    """
    type: Literal['Summers']
    Tc0_Summers: Optional[float] = None  # [K]
    Bc20_Summers: Optional[float] = None  # [T]
    Jc0_Summers: Optional[float] = None  # [A*T^0.5/m^2]


class Bordini(BaseModel):
    """
        Level 3: Class for cable Bordini's Nb3Sn fit
    """
    type: Literal['Bordini']
    Tc0_Bordini: Optional[float] = None  # [K]
    Bc20_Bordini: Optional[float] = None  # [T]
    C0_Bordini: Optional[float] = None  # [A*T/m^2]
    alpha_Bordini: Optional[float] = None  # [-]


class Nb3Sn_HFM(BaseModel):
    """
    Level 3: Class for cable HFM Nb3Sn fit
    """

    type: Literal["Nb3Sn_HFM"]
    Tc0_Nb3Sn_HFM: Optional[float] = None  # [K]
    Bc20_Nb3Sn_HFM: Optional[float] = None  # [T]
    C0_Nb3Sn_HFM: Optional[float] = None  # [A*T/m^2]
    alpha_Nb3Sn_HFM: Optional[float] = None  # [-]
    nu_Nb3Sn_HFM: Optional[float] = None  # [-]
    p_Nb3Sn_HFM: Optional[float] = None  # [-]
    q_Nb3Sn_HFM: Optional[float] = None  # [-]

class BSCCO_2212_LBNL(BaseModel):
    """
        Level 3: Class for cable Bi-2212 fit developed in LBNL
    """
    # only ad-hoc fit [T. Shen, D. Davis, E. Ravaioli with LBNL, Berkeley, CA]
    type: Literal['BSCCO_2212_LBNL']
    f_scaling_Jc_BSCCO2212: Optional[float] = None  # [-] used for the ad-hoc fit


# ------------------- Cable types ---------------------------#
class Mono(BaseModel):
    """
        Mono cable type: This is basically type of cable consisting of one strand - not really a cable
    """
    type: Literal['Mono']
    bare_cable_width: Optional[float] = None
    bare_cable_height_low: Optional[float] = None
    bare_cable_height_high: Optional[float] = None
    bare_cable_height_mean: Optional[float] = None
    th_insulation_along_width: Optional[float] = None
    th_insulation_along_height: Optional[float] = None
    # Fractions given with respect to the insulated conductor
    f_superconductor: Optional[float] = None
    f_stabilizer: Optional[float] = None  # (related to CuFraction in ProteCCT)
    f_insulation: Optional[float] = None
    f_inner_voids: Optional[float] = None
    f_outer_voids: Optional[float] = None
    # Available materials depend on the component and on the selected program
    material_insulation: Optional[str] = None
    material_inner_voids: Optional[str] = None
    material_outer_voids: Optional[str] = None


class Rutherford(BaseModel):
    """
        Rutherford cable type: for example LHC MB magnet cable
    """
    type: Literal['Rutherford']
    n_strands: Optional[int] = None
    n_strand_layers: Optional[int] = None
    n_strands_per_layers: Optional[int] = None
    bare_cable_width: Optional[float] = None
    bare_cable_height_low: Optional[float] = None
    bare_cable_height_high: Optional[float] = None
    bare_cable_height_mean: Optional[float] = None
    th_insulation_along_width: Optional[float] = None
    th_insulation_along_height: Optional[float] = None
    width_core: Optional[float] = None
    height_core: Optional[float] = None
    strand_twist_pitch: Optional[float] = None
    strand_twist_pitch_angle: Optional[float] = None
    Rc: Optional[float] = None
    Ra: Optional[float] = None
    # Fractions given with respect to the insulated conductor
    f_superconductor: Optional[float] = None
    f_stabilizer: Optional[float] = None  # (related to CuFraction in ProteCCT)
    f_insulation: Optional[float] = None
    f_inner_voids: Optional[float] = None
    f_outer_voids: Optional[float] = None
    f_core: Optional[float] = None
    # Available materials depend on the component and on the selected program
    material_insulation: Optional[str] = None
    material_inner_voids: Optional[str] = None
    material_outer_voids: Optional[str] = None
    material_core: Optional[str] = None


class Ribbon(BaseModel):
    """
        Ribbon cable type: This is basically type of cable consisting of one strand - not really a cable # TODO copy error, this is not MONO
    """
    type: Literal['Ribbon']
    n_strands: Optional[int] = None  # This defines the number of "strands" in the ribbon cable, which are physically glued but electrically in series
    bare_cable_width: Optional[float] = None  # refers to the strand width (rectangular) or diameter (round)
    bare_cable_height_low: Optional[float] = None
    bare_cable_height_high: Optional[float] = None
    bare_cable_height_mean: Optional[float] = None
    th_insulation_along_width: Optional[float] = None  # This defines the thickness of the insulation around each strand (DIFFERENT FROM ROXIE CADATA FILE)
    th_insulation_along_height: Optional[float] = None  # This defines the thickness of the insulation around each strand (DIFFERENT FROM ROXIE CADATA FILE)
    # Fractions given with respect to the insulated conductor
    f_superconductor: Optional[float] = None
    f_stabilizer: Optional[float] = None  # (related to CuFraction in ProteCCT)
    f_insulation: Optional[float] = None
    f_inner_voids: Optional[float] = None
    f_outer_voids: Optional[float] = None
    f_core: Optional[float] = None
    # Available materials depend on the component and on the selected program
    material_insulation: Optional[str] = None
    material_inner_voids: Optional[str] = None
    material_outer_voids: Optional[str] = None
    material_core: Optional[str] = None


# ------------------- Conductors ---------------------------#

class Round(BaseModel):
    """
        Level 2: Class for strand parameters
    """
    type: Literal['Round']
    diameter: Optional[float] = None  # ds_inGroup (LEDET), DConductor (BBQ), DStrand (ProteCCT)
    diameter_core:  Optional[float] = None  # dcore_inGroup (LEDET)
    diameter_filamentary:  Optional[float] = None  # dfilamentary_inGroup (LEDET)
    Cu_noCu_in_strand: Optional[float] = None
    RRR: Optional[Union[float, List[float]]] = Field(default=None, description="Residual resistivity ratio of the stabilizer. If a list of RRR is provided it needs to match in length the number of matrix regions in the geometry (typically 3)")
    T_ref_RRR_high: Optional[float] = None  # TupRRR (SIGMA), Reference temperature for RRR measurements
    T_ref_RRR_low: Optional[float] = None  # CURRENTLY NOT USED
    fil_twist_pitch: Optional[float] = None
    f_Rho_effective: Optional[float] = None
    material_superconductor: Optional[str] = None
    n_value_superconductor: Optional[float] = None
    ec_superconductor: Optional[float] = None
    minimum_jc_fraction: Optional[float] = Field(gt=0, le=1, default=None, description="Fraction of Jc(minimum_jc_field, T) to use as minimum Jc for the power law fit to avoid division by zero when Jc(B_local, T) decreases to zero."
                                                                                       "Typical value would be 0.001 (so the Jc_minimum is 0.1% of Jc(minimum_jc_field, T))"
                                                                                       "This fraction is only allowed to be greater than 0.0 and less than or equal to 1.0")
    minimum_jc_field: Optional[float] = Field(default=None, description="Magnetic flux density in tesla used for calculation of Jc(minimum_jc_field, T). This gets multiplied by minimum_jc_fraction and used as minimum Jc for the power law")

    material_stabilizer: Optional[str] = None
    rho_material_stabilizer: Optional[Union[str, float]] = Field(default='CFUN_rhoCu', description="Material function for resistivity of the stabilizer. Constant resistivity can be given as float.")
    rho_material_holes: Optional[Union[str, float]] = Field(default=None, description="Material function for resistivity of the holes in the filaments."
                                                                                      "Constant resistivity can be given as float, material name as a string or None or 0.0 to use 'air' in the holes.")
    k_material_stabilizer: Optional[Union[str, float]] = Field(default='CFUN_kCu', description="Thermal conductivity of the stabilizer.")
    Cv_material_stabilizer: Optional[Union[str, float]] = Field(default='CFUN_CvCu', description="Material function for specific heat of the stabilizer.")
    filament_diameter: Optional[float] = None  # df_inGroup (LEDET)
    filament_hole_diameter: Optional[float] = Field(default=None, description="Specifies round or hexagonal hole diameter inside the filament. If None or 0.0, no hole is created.")
    number_of_filaments: Optional[int] = None


class Rectangular(BaseModel):
    """
        Level 2: Class for strand parameters
    """
    type: Literal['Rectangular']
    bare_width: Optional[float] = None
    bare_height: Optional[float] = None
    Cu_noCu_in_strand: Optional[float] = None
    RRR: Optional[float] = None  # RRR_Cu_inGroup (LEDET), RRRStrand (ProteCCT)
    T_ref_RRR_high: Optional[float] = None  # TupRRR (SIGMA), Reference temperature for RRR measurements
    T_ref_RRR_low: Optional[float] = None  # CURRENTLY NOT USED
    fil_twist_pitch: Optional[float] = None
    f_Rho_effective: Optional[float] = None
    bare_corner_radius: Optional[float] = None
    material_superconductor: Optional[str] = Field(default=None, description="Material of the superconductor. E.g. Nb-Ti, Nb3Sn, etc.")
    n_value_superconductor: Optional[float] = Field(default=None, description="n value of the superconductor (for power law fit).")
    ec_superconductor: Optional[float] = Field(default=None, description="Critical electric field of the superconductor in V/m.")
    minimum_jc_fraction: Optional[float] = Field(gt=0, le=1, default=None, description="Fraction of Jc(minimum_jc_field, T) to use as minimum Jc for the power law"
                                                                                       " fit to avoid division by zero when Jc(B_local, T) decreases to zero."
                                                                           "Typical value would be 0.001 (so the Jc_minimum is 0.1% of Jc(minimum_jc_field, T))"
                                                                            "This fraction is only allowed to be greater than 0.0 and less than or equal to 1.0")
    minimum_jc_field: Optional[float] = Field(default=None, description="Magnetic flux density in tesla used for calculation of Jc(minimum_jc_field, T)."
                                                                        "This gets multiplied by minimum_jc_fraction and used as minimum Jc for the power law")
    minimum_jc_fraction: Optional[float] = Field(gt=0, le=1, default=None, description="Fraction of Jc(minimum_jc_field, T) to use as minimum Jc for the power law fit to avoid division by zero when Jc(B_local, T) decreases to zero."
                                                                           "Typical value would be 0.001 (so the Jc_minimum is 0.1% of Jc(minimum_jc_field, T))"
                                                                            "This fraction is only allowed to be greater than 0.0 and less than or equal to 1.0")
    minimum_jc_field: Optional[float] = Field(default=None, description="Magnetic flux density in tesla used for calculation of Jc(minimum_jc_field, T). This gets multiplied by minimum_jc_fraction and used as minimum Jc for the power law")
    k_material_superconductor: Optional[Union[str, float]] = Field(default=None, description="Thermal conductivity of the superconductor.")
    Cv_material_superconductor: Optional[Union[str, float]] = Field(default=None, description="Material function for specific heat of the superconductor.")
    material_stabilizer: Optional[str] = None
    k_material_stabilizer: Optional[Union[str, float]] = Field(default='CFUN_kCu', description="Thermal conductivity of the stabilizer.")
    Cv_material_stabilizer: Optional[Union[str, float]] = Field(default='CFUN_CvCu', description="Material function for specific heat of the stabilizer.")
    filament_diameter: Optional[float] = None  # df_inGroup (LEDET)
    number_of_filaments: Optional[int] = None

# ------------------- Conductors ---------------------------#

class Conductor(BaseModel):
    """
        Level 1: Class for conductor parameters
    """
    name: Optional[str] = None  # conductor name
    version: Optional[str] = None
    case: Optional[str] = None
    state: Optional[str] = None
    # For the below 3 parts see: https://gitlab.cern.ch/steam/steam_sdk/-/blob/master/docs/STEAM_SDK_Conductor_structure.svg
    cable: Union[Rutherford, Mono, Ribbon] = {'type': 'Rutherford'}     # TODO: Busbar, Rope, Roebel, CORC, TSTC, CICC
    strand: Union[Round, Rectangular] = {'type': 'Round'}       # TODO: Tape, WIC
    Jc_fit: Union[ConstantJc, Bottura, CUDI1, CUDI3, Summers, Bordini, Nb3Sn_HFM, BSCCO_2212_LBNL, Ic_A_NbTi] = {'type': 'CUDI1'}   # TODO: CUDI other numbers? , Roxie?


