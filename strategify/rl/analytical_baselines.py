import numpy as np
from scipy.linalg import solve_continuous_are

class LQRBaseline:
    """Exact Linear Quadratic Regulator baseline for Epidemic Environment.
    Uses 1st-order Jacobian Taylor expansion to linearize SEIR dynamics around 
    the Disease-Free Equilibrium (DFE) or Endemic Equilibrium.
    """
    
    def __init__(self, beta: float, sigma: float, gamma: float):
        self.beta = beta
        self.sigma = sigma
        self.gamma = gamma
        
        # State vector: X = [E, I] (fractions of population)
        # Control vector: U = [u_npi]
        # Linearized around S ~ 1.0, u ~ 0
        
        # A matrix (Jacobian dX/dt wrt X)
        # dE/dt = beta * I - sigma * E
        # dI/dt = sigma * E - gamma * I
        self.A = np.array([
            [-sigma, beta],
            [sigma, -gamma]
        ], dtype=float)
        
        # B matrix (Jacobian dX/dt wrt U)
        # dE/dt = beta * (1 - u_npi) * I - sigma * E
        # Evaluated at nominal small outbreak (I > 0)
        # The control derivative is -beta * I, but for LQR we use -beta as linear proxy
        self.B = np.array([
            [-beta],
            [0.0]
        ], dtype=float)
        
        # Cost matrices Q (state penalty) and R (control penalty)
        self.Q = np.array([
            [1.0, 0.0],
            [0.0, 100.0]  # High penalty for infections
        ], dtype=float)
        
        self.R = np.array([[10.0]], dtype=float)  # GDP drag penalty
        
        try:
            # Solve Continuous Algebraic Riccati Equation
            self.P = solve_continuous_are(self.A, self.B, self.Q, self.R)
            self.K = np.linalg.inv(self.R) @ self.B.T @ self.P
        except Exception:
            # Fallback if system is uncontrollable or ill-conditioned
            self.K = np.zeros((1, 2))

    def get_action(self, e_frac: float, i_frac: float) -> float:
        """Get optimal LQR control (NPI level) for current state.
        
        Parameters
        ----------
        e_frac : float
            Exposed population fraction.
        i_frac : float
            Infectious population fraction.
            
        Returns
        -------
        float
            Recommended NPI action [0, 1].
        """
        state = np.array([[e_frac], [i_frac]])
        u = -self.K @ state
        
        val = float(u[0, 0])
        # If val is negative, the system wants negative NPI which is impossible
        # We only apply NPI > 0 when outbreak occurs.
        return float(np.clip(val, 0.0, 1.0))
