OPENQASM 2.0;
include "qelib1.inc";
gate ccz q0,q1,q2 { p(pi/4) q1; p(pi/4) q2; cx q1,q2; u(0,0,-pi/4) q2; cx q1,q2; u(0,0,0) q2; cx q1,q0; p(-pi/4) q0; p(pi/4) q2; cx q0,q2; u(0,0,pi/4) q2; cx q0,q2; u(0,-pi/2,0) q2; cx q1,q0; p(pi/4) q0; p(pi/4) q2; cx q0,q2; u(0,0,-pi/4) q2; cx q0,q2; u(0,0,0) q2; }
gate ccz_o0 q0,q1,q2 { x q0; x q1; ccz q0,q1,q2; x q0; x q1; }
gate cz_o0 q0,q1 { x q0; cz q0,q1; x q0; }
gate gate_Q q0,q1,q2 { ccz_o0 q2,q1,q0; x q2; cz_o0 q0,q2; x q2; h q2; h q1; h q0; x q0; x q1; x q2; h q2; ccx q0,q1,q2; h q2; x q0; x q1; x q2; h q0; h q1; h q2; }
qreg q[3];
h q[0];
h q[1];
h q[2];
gate_Q q[0],q[1],q[2];
