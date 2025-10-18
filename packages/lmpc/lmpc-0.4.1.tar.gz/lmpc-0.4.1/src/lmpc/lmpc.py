import numpy as np

from types import ModuleType
from typing import cast
from juliacall import Main as jl
from juliacall import AnyValue

jl = cast(ModuleType, jl)
jl_version = (jl.VERSION.major, jl.VERSION.minor, jl.VERSION.patch)

jl.seval("using LinearMPC")
LinearMPC = jl.LinearMPC


class MPC:
    jl_mpc:AnyValue
    def __init__(self,A,B,Ts=None,Bd=None,Gd=None,C=np.zeros([0,0]),Dd=np.zeros([0,0]),Np=10, Nc=None):
        if Nc is None: Nc = Np
        if Ts is None or (Gd is not None and Bd is None):# discrete-time system
            if Gd is None: Gd = np.zeros([0,0]) 
            self.jl_mpc = LinearMPC.MPC(A,B,Gd=Gd,C=C,Dd=Dd,Np=Np,Nc=Nc)
        else:
            if Bd is None: Bd = np.zeros([0,0]) 
            self.jl_mpc = LinearMPC.MPC(A,B,Ts,Bd=Bd,C=C,Dd=Dd,Np=Np,Nc=Nc)

    def compute_control(self,x,r=None, d=None, uprev=None):
        return  LinearMPC.compute_control(self.jl_mpc, x, r = r, d=d, uprev=uprev)
    
    # Setting up problem 
    def setup(self):
        LinearMPC.setup_b(self.jl_mpc)

    def set_bounds(self, umin=np.zeros(0), umax=np.zeros(0), ymin=np.zeros(0), ymax=np.zeros(0)):
        LinearMPC.set_bounds_b(self.jl_mpc, umin = umin, umax = umax, ymin = ymin, ymax = ymax)

    def set_input_bounds(self, umin=np.zeros(0), umax=np.zeros(0)):
        LinearMPC.set_input_bounds_b(self.jl_mpc, umin = umin, umax = umax)

    def add_constraint(self,Ax = None, Au= None, 
                        Ar = np.zeros((0,0)), Aw = np.zeros((0,0)), 
                        Ad = np.zeros((0,0)), Aup = np.zeros((0,0)),
                        ub = np.zeros(0), lb = np.zeros(0),
                        ks = None, soft=False, binary=False, prio = 0):
        ks = range(2,self.jl_mpc.Np+1) if ks is None else [k+1 for k in ks]
        LinearMPC.add_constraint_b(self.jl_mpc, Ax=Ax, Au=Au, Ar=Ar, Ad=Ad, Aup=Aup, ub=ub, lb=lb,
                                 ks=ks, soft=soft, binary=binary, prio = prio)

    def set_output_bounds(self, ymin=np.zeros(0), ymax=np.zeros(0), ks =None, soft = True, binary=False, prio = 0):
        ks = range(2,self.jl_mpc.Np+1) if ks is None else [k+1 for k in ks]
        LinearMPC.set_output_bounds_b(self.jl_mpc,ymin=ymin,ymax=ymax, 
                                    ks=ks, soft=soft, binary=binary, prio=prio)

    def set_objective(self, Q=None, R=None ,Rr=None, S=None, Qf=None, Qfx=None):
        Q  = np.zeros((0,0)) if Q  is None else np.array(Q)
        R  = np.zeros((0,0)) if R  is None else np.array(R)
        Rr = np.zeros((0,0)) if Rr is None else np.array(Rr)
        S  = np.zeros((0,0)) if S  is None else np.array(S)
        Qf = np.zeros((0,0)) if Qf is None else np.array(Qf)
        Qfx = np.zeros((0,0)) if Qfx is None else np.array(Qfx)
        LinearMPC.set_weights_b(self.jl_mpc, Q=Q, R=R, Rr=Rr,S=S,Qf=Qf)

    def set_terminal_cost(self):
        LinearMPC.set_terminal_cost(self.jl_mpc)

    def set_prestabilizing_feedback(self, K=None):
        if K is not None:
            LinearMPC.set_prestabilizing_feedback_b(self.jl_mpc,K)
        else:
            LinearMPC.set_prestabilizing_feedback_b(self.jl_mpc)

    def move_block(self,move):
        LinearMPC.move_block_b(self.jl_mpc,move)

    def set_horizon(self,Np):
        LinearMPC.set_horizon_b(self.jl_mpc,Np)

    def set_binary_controls(self,bin_ids):
        LinearMPC.set_binary_controls_b(self.jl_mpc,bin_ids)

    def set_disturbance(self,wmin,wmax):
        LinearMPC.set_distrubance_b(self.jl_mpc,wmin,wmax)

    # code generation 
    def codegen(self, fname="mpc_workspace", dir="codegen", opt_settings=None, src=True, float_type="double"):
        LinearMPC.codegen(self.jl_mpc,fname=fname,dir=dir,opt_settings=opt_settings,src=src,float_type=float_type)

    # certification
    def certify(self, range=None, AS0=[], single_soft=True):
        return CertificationResult(LinearMPC.certify(self.jl_mpc,range=range,AS0=np.asarray(AS0,dtype=int),
                                                     single_soft=single_soft))

    def range(self, xmin=None,xmax=None,rmin=None,rmax=None,dmin=None,dmax=None,umin=None,umax=None):
        range = LinearMPC.ParameterRange(self.jl_mpc)
        if xmin is not None: range.xmin[:] = xmin
        if xmax is not None: range.xmax[:] = xmax
        if rmin is not None: range.rmin[:] = rmin
        if rmax is not None: range.rmax[:] = rmax
        if dmin is not None: range.dmin[:] = dmin
        if dmax is not None: range.dmax[:] = dmax
        if dmin is not None: range.umin[:] = umin
        if dmax is not None: range.umax[:] = umax
        return range

    def mpqp(self, singlesided = False, single_soft = False):
        mpqp_jl = LinearMPC.mpc2mpqp(self.jl_mpc,singlesided=singlesided, single_soft=single_soft)
        mpqp = {
                "jl_src" : mpqp_jl,
                "H": np.array(mpqp_jl.H,copy=False, order='F'),
                "f": np.array(mpqp_jl.f,copy=False, order='F'),
                "f_theta": np.array(mpqp_jl.f_theta,copy=False, order='F'),
                "H_theta": np.array(mpqp_jl.H_theta,copy=False, order='F'),
                "A": np.array(mpqp_jl.A,copy=False, order='F'),
                "W": np.array(mpqp_jl.W,copy=False, order='F'),
                "senses": np.array(mpqp_jl.senses,copy=False, order='F'),
                "prio": np.array(mpqp_jl.senses,copy=False, order='F'),
                "has_binaries": mpqp_jl.has_binaries
                #"break_points": np.array(mpqp_jl.break_points,copy=False, order='F')
                }
        if singlesided:
            mpqp["b"] = np.array(mpqp_jl.b,copy=False, order='F')
        else:
            mpqp["bu"] = np.array(mpqp_jl.bu,copy=False, order='F')
            mpqp["bl"] = np.array(mpqp_jl.bl,copy=False, order='F')
        return mpqp

# Explicit MPC
class ExplicitMPC:
    jl_mpc:AnyValue
    def __init__(self,mpc,range=None,build_tree=False):
        self.jl_mpc = LinearMPC.ExplicitMPC(mpc.jl_mpc,range=range,build_tree=build_tree)

    def plot_regions(self,th1,th2,x=None,r=None,d=None,uprev=None, show_fixed=True,show_zero=False):
        jl.display(LinearMPC.plot_regions(self.jl_mpc,th1,th2,x=x,r=r,d=d,uprev=uprev,
                                          show_fixed=show_fixed,show_zero=show_zero))

    def plot_feedback(self,u,th1,th2,x=None,r=None,d=None,uprev=None,show_fixed=True, show_zero=False):
        jl.display(LinearMPC.plot_feedback(self.jl_mpc,u,th1,th2,x=x,r=r,d=d,uprev=uprev,
                                           show_fixed=show_fixed,show_zero=show_zero))
    def codegen(self,fname="empc",dir="codegen", opt_settings=None, src=True, 
                float_type="double"):
        LinearMPC.codegen(self.jl_mpc,fname=fname,dir=dir,opt_settings=opt_settings,src=src,float_type=float_type)

# Certification 
class CertificationResult:
    jl_result:AnyValue
    def __init__(self,result):
        self.jl_result = result
    def plot(self,th1,th2,x=None,r=None,d=None,uprev=None, show_fixed=True,show_zero=False):
        jl.display(LinearMPC.plot(self.jl_result,th1,th2,x=x,r=r,d=d,uprev=uprev,
                                  show_fixed=show_fixed,show_zero=show_zero))
class Simulation:
    jl_sim:AnyValue
    ts: np.ndarray
    ys: np.ndarray
    us: np.ndarray
    xs: np.ndarray
    rs: np.ndarray
    ds: np.ndarray
    solve_times: np.ndarray

    def __init__(self,mpc,f=None,x0= None,N=1000, r=None,d=None):
        if x0 is None: x0 = np.zeros(mpc.jl_mpc.model.nx)
        if f  is None: 
            self.jl_sim = LinearMPC.Simulation(mpc.jl_mpc,x0=x0,N=N,r=r,d=d)
        else:
            self.jl_sim = LinearMPC.Simulation(f,mpc.jl_mpc,x0=x0,N=N,r=r,d=d)

        self.ts = np.array(self.jl_sim.ts,copy=False, order='F')
        self.ys = np.array(self.jl_sim.ys,copy=False, order='F')
        self.us = np.array(self.jl_sim.us,copy=False, order='F')
        self.xs = np.array(self.jl_sim.xs,copy=False, order='F')
        self.rs = np.array(self.jl_sim.rs,copy=False, order='F')
        self.ds = np.array(self.jl_sim.ds,copy=False, order='F')
        self.solve_times= np.array(self.jl_sim.solve_times,copy=False, order='F')
