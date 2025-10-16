window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
    processEscapes: true,
    processEnvironments: true,
    macros: {
      // The continuous variables.
      continuous: "x",
      // The lower bounds of the continuous variables.
      lowerBound: "\\ell",
      // The upper bounds of the continuous variables.
      upperBound: "u",
      // The categorical variables.
      categorical: "y",
      // The catalog of categorical variable values.
      catalog: "C",
      // A catalog value.
      catalogValue: "c",
      // The one-hot encodings of categorical variables values.
      oneHot: "\\alpha",
      // The relaxed encodings of categorical variables values.
      relaxed: "\\tilde{\\oneHot}",
      // The initial objective function.
      objective: "f",
      // The initial constraint function.
      constraint: "g",
      // The parametrization of the objective with one-hot encodings.
      oneHotObjective: "\\hat{\\objective}",
      // The parametrization of the contraint with one-hot encodings.
      oneHotConstraint: "\\hat{\\constraint}",
      // The upper level objective function.
      // #1 The value of the one-hot encoding.
      upperObjective: ["\\oneHotObjective(\\continuous^*(#1), #1)", 1],
      // An underestimator of the objective function.
      objectiveUnderestimator: "\\bar{\\objective}",
      // The adaptive convexification of the objective function.
      objectiveConvexification: "\\check{\\objective}"
    }
  },
  options: {
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex"
  }
};

document$.subscribe(() => {
  MathJax.typesetPromise()
})
