import numpy as np

class CoxPHPredictorWithUncertainty:
    def __init__(self, hazard_ratios, hazard_ratios_uncertainties):
        """
        Initialize the CoxPHPredictorWithUncertainty with hazard ratios and their uncertainties.

        Args:
        - hazard_ratios (dict): A dictionary containing the hazard ratios for each covariate.
                                The keys are the names of the covariates, and the values are
                                the corresponding hazard ratios.
        - hazard_ratios_uncertainties (dict): A dictionary containing the uncertainties (e.g., standard errors)
                                              associated with the hazard ratios.
        """
        self.hazard_ratios = hazard_ratios
        self.hazard_ratios_uncertainties = hazard_ratios_uncertainties

    def predict_cox_output_with_uncertainty(self, covariates):
        """
        Predict survival probability for a given set of covariates with uncertainties.

        Args:
        - covariates (dict): A dictionary containing the values of covariates for an individual.
                             The keys are the names of the covariates, and the values are
                             the corresponding covariate values.

        Returns:
        - cox_output (float): The predicted survival probability for the individual.
        - uncertainty (float): The uncertainty associated with the predicted survival probability.
        """
        hazard_sum = 0
        hazard_sum_uncertainty = 0
        
        for covariate, value in covariates.items():
            if covariate in self.hazard_ratios:
                hazard_sum += self.hazard_ratios[covariate] * value
                hazard_sum_uncertainty += (self.hazard_ratios_uncertainties[covariate] * value) ** 2
        
        cox_output = np.exp(-hazard_sum)
        uncertainty = np.sqrt(hazard_sum_uncertainty)
        
        return cox_output, uncertainty

# Example usage:
# Load saved hazard ratios and uncertainties (replace this with your method of loading coefficients and uncertainties)
# saved_hazard_ratios = {
#     'age': 0.02,
#     'gender': 0.5,
#     'treatment': -0.3
# }
# saved_hazard_ratios_uncertainties = {
#     'age': 0.005,
#     'gender': 0.1,
#     'treatment': 0.02
# }

# # Initialize the predictor with the saved hazard ratios and uncertainties
# cox_predictor_with_uncertainty = CoxPHPredictorWithUncertainty(saved_hazard_ratios, saved_hazard_ratios_uncertainties)

# # Define covariates for an individual
# individual_covariates = {
#     'age': 65,
#     'gender': 1,  # 1 for male, 0 for female
#     'treatment': 1  # 1 for received treatment, 0 for no treatment
# }

# # Predict survival probability for the individual with uncertainties
# predicted_cox_output, uncertainty = cox_predictor_with_uncertainty.predict_cox_output_with_uncertainty(individual_covariates)
# print("Predicted survival probability:", predicted_cox_output)
# print("Uncertainty:", uncertainty)