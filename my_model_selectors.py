import math
import statistics
import warnings

import numpy as np
from hmmlearn.hmm import GaussianHMM
from sklearn.model_selection import KFold
from asl_utils import combine_sequences


class ModelSelector(object):
    '''
    base class for model selection (strategy design pattern)
    '''

    def __init__(self, all_word_sequences: dict, all_word_Xlengths: dict, this_word: str,
                 n_constant=3,
                 min_n_components=2, max_n_components=10,
                 random_state=14, verbose=False):
        self.words = all_word_sequences
        self.hwords = all_word_Xlengths
        self.sequences = all_word_sequences[this_word]
        self.X, self.lengths = all_word_Xlengths[this_word]
        self.this_word = this_word
        self.n_constant = n_constant
        self.min_n_components = min_n_components
        self.max_n_components = max_n_components
        self.random_state = random_state
        self.verbose = verbose

    def select(self):
        raise NotImplementedError

    def base_model(self, num_states):
        # with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        # warnings.filterwarnings("ignore", category=RuntimeWarning)
        try:
            hmm_model = GaussianHMM(n_components=num_states, covariance_type="diag", n_iter=1000,
                                    random_state=self.random_state, verbose=False).fit(self.X, self.lengths)
            if self.verbose:
                print("model created for {} with {} states".format(self.this_word, num_states))
            return hmm_model
        except:
            if self.verbose:
                print("failure on {} with {} states".format(self.this_word, num_states))
            return None


class SelectorConstant(ModelSelector):
    """ select the model with value self.n_constant

    """

    def select(self):
        """ select based on n_constant value

        :return: GaussianHMM object
        """
        best_num_components = self.n_constant
        return self.base_model(best_num_components)


class SelectorBIC(ModelSelector):
    """ select the model with the lowest Bayesian Information Criterion(BIC) score

    http://www2.imm.dtu.dk/courses/02433/doc/ch6_slides.pdf
    Bayesian information criteria: BIC = -2 * logL + p * logN
    """
    def select(self):
        """ select the best model for self.this_word based on
        BIC score for n between self.min_n_components and self.max_n_components

        :return: GaussianHMM object
        """
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        # TODO implement model selection based on BIC scores


        #logL = model.score(X, lengths)
    def calc_num_free_params(self, num_states, num_data_points):
        return ( num_states ** 2 ) + ( 2 * num_states * num_data_points ) - 1

    def calc_score_bic(self, log_likelihood, num_free_params, num_data_points):
        return (-2 * log_likelihood) + (num_free_params * np.log(num_data_points))

    def calc_best_score_bic(self, score_bics):
        # Min of list of lists comparing each item by value at index 0
        return min(score_bics, key = lambda x: x[0])

    def select(self):
        """ Select best model for self.this_word based on BIC score
        for n between self.min_n_components and self.max_n_components
        :return: GaussianHMM object
        """
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        score_bics = []
        for num_states in range(self.min_n_components, self.max_n_components + 1):
            try:
                hmm_model = self.base_model(num_states)
                log_likelihood = hmm_model.score(self.X, self.lengths)
                num_data_points = sum(self.lengths)
                num_free_params = self.calc_num_free_params(num_states, num_data_points)
                score_bic = self.calc_score_bic(log_likelihood, num_free_params, num_data_points)
                score_bics.append(tuple([score_bic, hmm_model]))
            except:
                pass
        return self.calc_best_score_bic(score_bics)[1] if score_bics else None


class SelectorDIC(ModelSelector):
    ''' select best model based on Discriminative Information Criterion

    Biem, Alain. "A model selection criterion for classification: Application to hmm topology optimization."
    Document Analysis and Recognition, 2003. Proceedings. Seventh International Conference on. IEEE, 2003.
    http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.58.6208&rep=rep1&type=pdf
    https://pdfs.semanticscholar.org/ed3d/7c4a5f607201f3848d4c02dd9ba17c791fc2.pdf
    DIC = log(P(X(i)) - 1/(M-1)SUM(log(P(X(all but i))
    '''

    def select(self):
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        # TODO implement model selection based on DIC scores
        raise NotImplementedError


class SelectorCV(ModelSelector):
    ''' select best model based on average log Likelihood of cross-validation folds

    '''

    def select(self):
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        # TODO implement model selection using CV

        max_logL = -np.inf
        selected_model = None
        n_splits = min(3, len(self.sequences))
        print('**** {} -- num sequences:{}, n_splits:{}, max states:{}'.format(self.this_word, len(self.sequences),
                                                                n_splits, self.max_n_components+1))

        for num_states in range(self.min_n_components, self.max_n_components+1):
            print('    num_states:{}'.format(num_states))
            for cv_train_idx, cv_test_idx in KFold(n_splits=n_splits, random_state=self.random_state).split(self.sequences):
                try:
                    # Train
                    self.X, self.lengths = combine_sequences(cv_train_idx, self.sequences)
                    model = self.base_model(num_states)
                except:
                    print('        xxxx Train failed. train:{}'.format(cv_train_idx))
                    continue
                try:
                    # Validate
                    X_test, test_len = combine_sequences(cv_test_idx, self.sequences)
                    logL = model.score(X_test, test_len)
                    if logL > max_logL:
                        max_logL = logL
                        selected_model = model
                    print('        Max:{:,.0f}, logL:{:,.0f}, train_len:{}, test_len:{}, model states:{}'\
                                    .format(max_logL, logL, len(cv_train_idx), len(cv_test_idx),
                                            selected_model.n_components))

                except:
                    print('        xxxx Validation failed. train:{}, test:{}'.format(cv_train_idx,cv_test_idx))
                    continue

        return selected_model



