<!--
Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com

This work is licensed under the Creative Commons Attribution-ShareAlike 4.0
International License. To view a copy of this license, visit
http://creativecommons.org/licenses/by-sa/4.0/ or send a letter to Creative
Commons, PO Box 1866, Mountain View, CA 94042, USA.
-->
# User guide

Bilevel Outer Approximation (a.k.a. Bilevel OA)
combines the formulation
[Benders][gemseo_bilevel_outer_approximation.formulations.benders.Benders]
with a dedicated optimization library
[OuterApproximationLibrary][gemseo_bilevel_outer_approximation.algos.opt.outer_approximation.outer_approximation.OuterApproximationLibrary]
to solve MDO problems depending on both continuous variables $\continuous$ and categorical variables $\categorical$.

Each of the $n_{\categorical}$ categorical variable is assumed to take values in a *catalogue* $\catalog$ of choices:
$\catalog = \{ \catalogValue_1, \catalogValue_2, \ldots \}$.

$$\begin{align}
& \textsf{Minimize}    & & \objective(\continuous, \categorical) \\
& \textsf{relative to} & & \lowerBound \le \continuous \le \upperBound \textsf{ and } \categorical \textsf{ in } \catalog^{n_{\categorical}} \\
& \textsf{subject to}  & & \constraint(\continuous, \categorical) \le 0.
\end{align}$$

## One-hot encoding

In order to rewrite the problem as a mixed-integer problem,
the categorical variables are parametrized with *one-hot encoders*:
$\{0, 1\}$-valued vectors $\oneHot_i$ of size $n_{\catalog}$ with exactly one coordinate equal to one,
indicating a choice in catalog $\catalog$.
Categorical variable $\categorical_i$ is then parametrized as $\categorical_i(\oneHot_i) = \catalogValue_j$,
where $j$ is the only index such that $\oneHot_{i, j} = 1$.
We denote $\oneHotObjective$ and $\oneHotConstraint$ the parametrizations of the objective and constraint functions,
so that $\oneHotObjective(\continuous, \oneHot) = \objective(\continuous, \categorical(\oneHot))$ and $\oneHotConstraint(\continuous, \oneHot) = \constraint(\continuous, \categorical(\oneHot))$.
The problem becomes the following.

$$\begin{align}
& \textsf{Minimize}    & & \oneHotObjective(\continuous, \oneHot) \\
& \textsf{relative to} & & \lowerBound \le \continuous \le \upperBound \textsf{ and }
                           \oneHot \textsf{ in } \{ 0, 1 \}^{n_{\categorical} \times n_{\catalog}}
                           \textsf{ with } \oneHot \mathbb{1}_{n_{\catalog}} = \mathbb{1}_{n_{\categorical}} \\
& \textsf{subject to}  & & \oneHotConstraint(\continuous, \oneHot) \le 0.
\end{align}$$

## Bilevel formulation

The problem is reformulated as a bilevel problem:
the binary variables $\oneHot$ are handled at the *upper level*,
while the *lower level* (parametrized by $\oneHot$) handles the continuous variables $\continuous$.

$$\begin{align}
& \textsf{Minimize}    & & \upperObjective{\oneHot} \\
& \textsf{relative to} & & \oneHot \textsf{ in } \{ 0, 1 \}^{n_{\categorical} \times n_{\catalog}}
                           \textsf{ with } \oneHot \mathbb{1}_{n_{\catalog}} = \mathbb{1}_{n_{\categorical}} \\
%                           \textsf{ with } \sum_{j=1}^{n_{\catalog}} \oneHot_{i, j} = 1, \; i = 1, \dots, n_{\categorical} \\
& \textsf{subject to}  & & \continuous^*(\oneHot) = \operatorname{argmin}
                           \big\{ \oneHotObjective(\continuous, \oneHot) : \lowerBound \le \continuous \le \upperBound \textsf{ and } \oneHotConstraint(\continuous, \oneHot) \le 0 \big\}.
\tag{P}
\end{align}$$

<!-- $$\begin{align}
& \textsf{Minimize}    & & \objective(\continuous^*, \categorical) \\
& \textsf{relative to} & & \categorical \textsf{ in } \catalog^{n_{\categorical}} \\
& \textsf{subject to}  & & \continuous^* \in \operatorname{argmin}\{ \objective(\continuous, \categorical) : \lowerBound \le \continuous \le \upperBound \textsf{ and } \constraint(\continuous, \categorical) \le 0 \}.
\end{align}$$ -->

## Outer approximation

!!! warning "Relaxability and smoothness assumptions"
    For a given $\continuous$ and *relaxed* values $\relaxed$ in $[0, 1]^{n_{\categorical} \times n_{\catalog}}$
    with $\relaxed \mathbb{1}_{n_{\catalog}} = \mathbb{1}_{n_{\categorical}}$,

    *   the function values $\oneHotObjective(\continuous, \relaxed)$ and $\oneHotConstraint(\continuous, \relaxed)$
        are assumed to be computable,
    *   the derivatives $\partial_{\oneHot}\oneHotObjective(\continuous, \relaxed)$
        and $\partial_{\oneHot}\oneHotConstraint(\continuous, \relaxed)$
        are assumed to be computable.

Let us a consider iteration $k$ of the algorithm.
Denote $\oneHot_k$ the one-hot encoding selected at the upper level
and denote $\continuous^*(\oneHot_k)$ the unique solution of the lower level problem.
The post-optimal sensitivities
$\frac{\textup{d}\upperObjective{\relaxed}}{\textup{d}\relaxed}
\Big|_{\relaxed = \oneHot_k}$
can be computed using Fiacco's theorem,
and we define a linear mapping $\objectiveUnderestimator_k$ that intersects the upper level objective
at $\oneHot_k$ as follows:

$$\begin{align}
\objectiveUnderestimator_k(\oneHot)
=
\upperObjective{\oneHot_k}
+
\frac{\textup{d}\upperObjective{\relaxed}}{\textup{d}\relaxed}
\Bigg|_{\relaxed = \oneHot_k} : (\oneHot - \oneHot_k),
\end{align}$$

where "$:$" denotes the [Frobenius inner product](https://en.wikipedia.org/wiki/Frobenius_inner_product).
The *outer approximation* of $\upperObjective{\cdotp}$ is the function $\eta_k$ defined as follows:

$$\begin{align}
\eta_k(\oneHot)
=
\max_{l = 1, \, \dots, \, k} \objectiveUnderestimator_l(\oneHot).
\end{align}$$

!!! note "Convex case"
    If $\upperObjective{\cdotp}$ is convex
    then it holds $\upperObjective{\oneHot} \ge \objectiveUnderestimator_k(\oneHot)$ for all $\oneHot$.
    Therefore $\upperObjective{\oneHot} \ge \eta_k(\oneHot)$ for all $\oneHot$
    (with equality at each $\oneHot_k$)
    hence the name "outer approximation".

The upper level problem is solved by replacing the objective function with the current outer approximation:

$$\begin{align}
& \textsf{minimize}    & & \eta_k(\oneHot) \\
& \textsf{relative to} & & \oneHot \textsf{ in } \{ 0, 1 \}^{n_{\categorical} \times n_{\catalog}}
                           \textsf{ with } \oneHot \mathbb{1}_{n_{\catalog}} = \mathbb{1}_{n_{\categorical}} \\
%                           \textsf{ with } \sum_{j=1}^{n_{\catalog}} \oneHot_{i, j} = 1, \; i = 1, \dots, n_{\categorical} \\
& \textsf{subject to}  & & \oneHot \not\in S_k^{\mathrm{infeasible}}.
\end{align}$$

## Convexification

We explore approaches to replace the objective function of the upper level problem $(P)$
with a convex function.

### Underestimator

A straightforward idea consists in replacing the objective of the upper level problem $(P)$
with a parametrized function that matches the objective on one-hot encodings
and that is convex if its parameter $\kappa$ is big enough:

$$\begin{align}
\tilde{f}(\oneHot)
=
\upperObjective{\oneHot}
+
\frac{\kappa}{n_{\categorical}} \oneHot : (\oneHot - \mathbb{1}).
\end{align}$$

### Post-optimal sensitivity amplification

$$\begin{align}
\objectiveUnderestimator^\xi_k(\oneHot)
=
\upperObjective{\oneHot_k}
+
\left[
A_k \circ
\frac{\textup{d}\upperObjective{\relaxed}}{\textup{d}\relaxed}
\Bigg|_{\relaxed = \oneHot_k}
\right]
: (\oneHot - \oneHot_k),
\end{align}$$

where

$$\begin{align}
[A_k]_{i, j}
=
\begin{cases}
\xi
&
\text{if } [\oneHot_k]_{i, j} = 0
\text{ and } \left[
    \frac{\textup{d}\upperObjective{\relaxed}}{\textup{d}\relaxed}
    \bigg|_{\relaxed = \oneHot_k}
    \right]_{i, j} < 0
\\
\xi
&
\text{if } [\oneHot_k]_{i, j} = 1
\text{ and } \left[
    \frac{\textup{d}\upperObjective{\relaxed}}{\textup{d}\relaxed}
    \bigg|_{\relaxed = \oneHot_k}
    \right]_{i, j} > 0
\\
1 & \text{otherwise}.
\end{cases}
\end{align}$$

### Adaptive convexification

If $\upperObjective{\cdotp}$ is not convex,
$\objectiveUnderestimator_k$ is not guaranteed to be an underestimator.
Adaptive convexification consists in adaptating the slope of $\objectiveUnderestimator_k$
to build a function that underestimates $\upperObjective{\cdotp}$
at least at the previously explored one-hot encoding $\oneHot_1, \dots, \oneHot_M$.


$$\begin{align}
\objectiveConvexification_k(\oneHot)
= & \;
\upperObjective{\oneHot_k}
+
\left[
\frac{\textup{d}\upperObjective{\relaxed}}{\textup{d}\relaxed}
\Bigg|_{\relaxed = \oneHot_k}
+
\sum_{s=1}^M \gamma_s (\oneHot_s - \oneHot_k)
\right]
: (\oneHot - \oneHot_k)
\\
= & \;
\objectiveUnderestimator_k(\oneHot)
+
\sum_{s=1}^M \gamma_s (\oneHot_s - \oneHot_k) : (\oneHot - \oneHot_k)
.
\end{align}$$


## Logigram

![Logigram](logigram.png)
