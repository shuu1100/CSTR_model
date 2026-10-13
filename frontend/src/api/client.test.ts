import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api, ApiError } from './client';
import { SteadyStateRequest, DynamicSimulationRequest } from './types';

describe('Frontend API Client & Contracts', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('ApiError preserves status and message formatting', () => {
    const err = new ApiError(422, 'Invalid reaction order 4', { detail: 'Invalid reaction order 4' });
    expect(err.name).toBe('ApiError');
    expect(err.status).toBe(422);
    expect(err.message).toBe('Invalid reaction order 4');
    expect(err.details).toEqual({ detail: 'Invalid reaction order 4' });
  });

  it('runSteadyState sends valid request and receives response', async () => {
    const mockResponse = {
      model_id: 'isothermal_cstr_order_1',
      normalized_inputs: { V: 10.0, Q: 1.0, C_A_in: 1.0, order: 1, k: 0.15 },
      outputs: {
        tau: 10.0,
        C_A_ss: 0.40,
        conversion: 0.60,
        reaction_rate_ss: -0.06,
        residual: 0.0,
      },
      units: { V: 'L', Q: 'L/min', C_A_in: 'mol/L', tau: 'min', C_A_ss: 'mol/L' },
      assumptions: ['Ideal CSTR'],
      diagnostics: { material_balance_closed: true },
      warnings: [],
    };

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    } as Response);

    const req: SteadyStateRequest = {
      V: 10.0,
      Q: 1.0,
      C_A_in: 1.0,
      order: 1,
      k: 0.15,
    };

    const res = await api.runSteadyState(req);

    expect(fetchSpy).toHaveBeenCalledTimes(1);
    const [url, options] = fetchSpy.mock.calls[0];
    expect(url).toContain('/api/v1/simulations/steady-state');
    expect(options?.method).toBe('POST');
    expect(JSON.parse(options?.body as string)).toEqual(req);

    expect(res.outputs.tau).toBe(10.0);
    expect(res.outputs.C_A_ss).toBe(0.40);
    expect(res.outputs.conversion).toBe(0.60);
    expect(res.diagnostics.material_balance_closed).toBe(true);
  });

  it('runDynamicSimulation handles backend errors gracefully', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: false,
      status: 422,
      statusText: 'Unprocessable Entity',
      json: async () => ({ detail: 'Parameter V must be strictly positive' }),
    } as Response);

    const req: DynamicSimulationRequest = {
      C_A_0: 0.5,
      C_A_in: 2.0,
      V: -5.0,
      Q: 1.0,
      order: 1,
      k: 0.15,
      t_final: 50.0,
      n_points: 51,
      solver_method: 'RK45',
    };

    await expect(api.runDynamicSimulation(req)).rejects.toThrow(
      'Parameter V must be strictly positive'
    );
  });

  it('Canonical oracle values conform to GLOBAL-INSTRUCTIONS specifications', () => {
    const oracle = {
      V: 10.0,
      Q: 1.0,
      k: 0.15,
      C_A_in: 1.0,
      expectedTau: 10.0,
      expectedCss: 0.40,
      expectedConversion: 0.60,
    };

    const tau = oracle.V / oracle.Q;
    const Da = oracle.k * tau;
    const Css = oracle.C_A_in / (1.0 + Da);
    const conv = (oracle.C_A_in - Css) / oracle.C_A_in;

    expect(tau).toBe(oracle.expectedTau);
    expect(Css).toBeCloseTo(oracle.expectedCss, 6);
    expect(conv).toBeCloseTo(oracle.expectedConversion, 6);
  });
});
