/**
 * Aurora OSI v3 - Physics Utilities for Frontend
 * Physics-based calculations and constraints
 */

/**
 * Gravity field calculation
 * F = G * m1 * m2 / r²
 */
export function calculateGravityField(
  mass1: number,
  mass2: number,
  distance: number,
  G: number = 6.674e-11
): number {
  if (distance === 0) return Infinity;
  return (G * mass1 * mass2) / (distance * distance);
}

/**
 * Seismic velocity from elastic parameters
 * Vp = sqrt((λ + 2μ) / ρ)
 * Vs = sqrt(μ / ρ)
 */
export interface SeismicVelocities {
  vp: number;
  vs: number;
  poisson_ratio: number;
}

export function calculateSeismicVelocities(
  lambda: number,
  mu: number,
  density: number
): SeismicVelocities {
  const vp = Math.sqrt((lambda + 2 * mu) / density);
  const vs = Math.sqrt(mu / density);
  const poisson = (lambda - mu) / (2 * (lambda + mu));

  return {
    vp,
    vs,
    poisson_ratio: poisson,
  };
}

/**
 * Temperature calculation at depth
 * T(z) = T_surface + gradient * z
 */
export function temperatureAtDepth(
  depth: number,
  surfaceTemp: number = 15,
  gradient: number = 0.025
): number {
  return surfaceTemp + gradient * depth;
}

/**
 * Density from Gardner's equation
 * ρ = 0.31 * Vp^0.25
 */
export function densityFromGardner(vp: number): number {
  if (vp <= 0) return 2700;
  return 0.31 * Math.pow(vp, 0.25) * 1000; // in kg/m³
}

/**
 * Acoustic impedance
 * Z = Vp * ρ
 */
export function acousticImpedance(vp: number, density: number): number {
  return vp * density;
}

/**
 * Elastic impedance at angle θ
 * EI = Vp*ρ*sin²θ - 4*Vs²*ρ*sin²θ*cos²θ + Vp*ρ*cos²θ
 */
export function elasticImpedance(
  vp: number,
  vs: number,
  density: number,
  angleDegrees: number
): number {
  const angle = (angleDegrees * Math.PI) / 180;
  const sin2 = Math.sin(angle) ** 2;
  const cos2 = Math.cos(angle) ** 2;

  return (
    vp * density * sin2 -
    4 * vs * vs * density * sin2 * cos2 +
    vp * density * cos2
  );
}

/**
 * Reflection coefficient (Zoeppritz at normal incidence)
 * R = (Z2 - Z1) / (Z2 + Z1)
 */
export function reflectionCoefficient(z1: number, z2: number): number {
  if (z1 + z2 === 0) return 0;
  return (z2 - z1) / (z2 + z1);
}

/**
 * Thermal conductivity correction with temperature
 * k(T) = k_ref * (1 - α * ΔT)
 */
export function thermalConductivity(
  temperature: number,
  kRef: number = 2.5,
  alpha: number = 0.003
): number {
  const deltaT = temperature - 25;
  return kRef * (1 - alpha * deltaT);
}

/**
 * Darcy velocity in porous media
 * v = -(k/μ) * ∇P
 */
export function darcyVelocity(
  permeability: number,
  viscosity: number,
  pressureGradient: number
): number {
  if (viscosity === 0) return 0;
  return -(permeability / viscosity) * pressureGradient;
}

/**
 * Capillary pressure (Young-Laplace equation)
 * Pc = 2σ*cos(θ) / r
 */
export function capillaryPressure(
  surfaceTension: number,
  contactAngle: number,
  poreRadius: number
): number {
  if (poreRadius === 0) return Infinity;
  const angleRad = (contactAngle * Math.PI) / 180;
  return (2 * surfaceTension * Math.cos(angleRad)) / poreRadius;
}

/**
 * Saturation from Brooks-Corey model
 * S = ((P_e / P_c)^λ) if P_c > P_e, else 1
 */
export function saturationBrooksCorey(
  capillaryPressure: number,
  entryPressure: number = 1000,
  lambda: number = 2.0
): number {
  if (capillaryPressure <= entryPressure) return 1;
  return Math.pow(entryPressure / capillaryPressure, lambda);
}

/**
 * Relative permeability
 * kr = ((S - Sr) / (1 - Sr))^n
 */
export function relativePermeability(
  saturation: number,
  saturationResidual: number = 0.2,
  exponent: number = 2.0
): number {
  const normalized =
    (saturation - saturationResidual) / (1 - saturationResidual);
  const clipped = Math.max(0, Math.min(1, normalized));
  return Math.pow(clipped, exponent);
}

/**
 * Magnetic susceptibility conversion
 * SI units <-> CGS units
 */
export function susceptibilitySIToCGS(siValue: number): number {
  return siValue / (4 * Math.PI);
}

export function susceptibilityCGSToSI(cgsValue: number): number {
  return cgsValue * 4 * Math.PI;
}

/**
 * Total magnetic intensity from inclination/declination
 */
export interface MagneticField {
  bx: number;
  by: number;
  bz: number;
  magnitude: number;
}

export function calculateMagneticField(
  inclination: number,
  declination: number,
  amplitude: number
): MagneticField {
  const incRad = (inclination * Math.PI) / 180;
  const decRad = (declination * Math.PI) / 180;

  const bx = amplitude * Math.cos(incRad) * Math.cos(decRad);
  const by = amplitude * Math.cos(incRad) * Math.sin(decRad);
  const bz = amplitude * Math.sin(incRad);

  return {
    bx,
    by,
    bz,
    magnitude: amplitude,
  };
}

/**
 * Poisson's equation residual (gravity field constraint)
 * ∇²Φ = 4πGρ
 */
export function poissonResidual(
  laplacian: number,
  density: number,
  G: number = 6.674e-11
): number {
  return laplacian - 4 * Math.PI * G * density;
}

/**
 * Heat equation constraint
 * ρc(∂T/∂t) = ∇·(k∇T) + Q
 */
export function heatEquationResidual(
  tempDot: number,
  heatDiffusion: number,
  heatSource: number,
  density: number,
  specificHeat: number
): number {
  return density * specificHeat * tempDot - (heatDiffusion + heatSource);
}

/**
 * NDVI calculation from satellite bands
 * NDVI = (NIR - RED) / (NIR + RED)
 */
export function calculateNDVI(nir: number, red: number): number {
  if (nir + red === 0) return 0;
  return (nir - red) / (nir + red);
}

/**
 * NDMI calculation (moisture index)
 * NDMI = (NIR - SWIR) / (NIR + SWIR)
 */
export function calculateNDMI(nir: number, swir: number): number {
  if (nir + swir === 0) return 0;
  return (nir - swir) / (nir + swir);
}

/**
 * Clay minerals index
 * CMI = SWIR2 / SWIR1
 */
export function calculateCMI(swir2: number, swir1: number): number {
  if (swir1 === 0) return 0;
  return swir2 / swir1;
}

/**
 * Iron oxide index
 * IOR = RED / SWIR1
 */
export function calculateIOR(red: number, swir1: number): number {
  if (swir1 === 0) return 0;
  return red / swir1;
}

/**
 * Convert wavelength to frequency
 * f = c / λ
 */
export function wavelengthToFrequency(wavelengthNm: number): number {
  const c = 3e8; // m/s
  const wavelengthM = wavelengthNm / 1e9;
  if (wavelengthM === 0) return 0;
  return c / wavelengthM;
}

/**
 * Calculate energy from frequency
 * E = h * f
 */
export function frequencyToEnergy(frequencyHz: number): number {
  const h = 6.626e-34; // Planck's constant
  return h * frequencyHz;
}

/**
 * Planck's law for blackbody radiation
 */
export function plancksLaw(
  wavelengthM: number,
  temperatureK: number
): number {
  const h = 6.626e-34;
  const c = 3e8;
  const kb = 1.38e-23;

  if (wavelengthM === 0 || temperatureK === 0) return 0;

  const numerator = 2 * h * c * c;
  const denominator =
    Math.pow(wavelengthM, 5) *
    (Math.exp((h * c) / (wavelengthM * kb * temperatureK)) - 1);

  return numerator / denominator;
}

/**
 * Stress tensor invariants
 */
export function stressInvariants(
  sigma: [[number, number, number], [number, number, number], [number, number, number]]
) {
  const s11 = sigma[0][0];
  const s22 = sigma[1][1];
  const s33 = sigma[2][2];
  const s12 = sigma[0][1];
  const s23 = sigma[1][2];
  const s31 = sigma[2][0];

  const I1 = s11 + s22 + s33;
  const I2 = s11 * s22 + s22 * s33 + s33 * s11 - s12 * s12 - s23 * s23 - s31 * s31;
  const I3 =
    s11 * s22 * s33 +
    2 * s12 * s23 * s31 -
    s11 * s23 * s23 -
    s22 * s31 * s31 -
    s33 * s12 * s12;

  return { I1, I2, I3 };
}

export default {
  calculateGravityField,
  calculateSeismicVelocities,
  temperatureAtDepth,
  densityFromGardner,
  acousticImpedance,
  elasticImpedance,
  reflectionCoefficient,
  thermalConductivity,
  darcyVelocity,
  capillaryPressure,
  saturationBrooksCorey,
  relativePermeability,
  calculateMagneticField,
  calculateNDVI,
  calculateNDMI,
  calculateCMI,
};
