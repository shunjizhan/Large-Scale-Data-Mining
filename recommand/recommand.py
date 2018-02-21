import csv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
import pprint as pp
import operator

from surprise import Dataset
from surprise import Reader
from surprise import accuracy
from surprise.model_selection import KFold
from surprise.model_selection import train_test_split
from surprise.prediction_algorithms import knns
from surprise.prediction_algorithms import matrix_factorization
from sklearn.metrics import roc_curve
from sklearn.metrics import auc


def plot_freqency(d, msg=None):
    sorted_ = sorted(d.items(), key=operator.itemgetter(1), reverse=True)
    ids, ratings = zip(*sorted_)
    plot_bar(ratings, msg)


def plot_bar(arr, msg=None):
    plt.bar(np.arange(len(arr)), arr)
    plt.title(msg)
    plt.show()


def read_data():
    # Loading Ratings.csv
    ratings = {}
    sparse = {}
    ratings['user'], sparse['user'] = [], []
    ratings['movie'], sparse['movie'] = [], []
    ratings['rating'] = []
    filename = 'recommand/ml-latest-small/ratings.csv'
    with open(filename, "rt") as input:
        reader = csv.reader(input, delimiter=',', quoting=csv.QUOTE_NONE)
        next(reader, None)  # skip header
        for line in reader:
            ratings['user'].append(float(line[0]))
            ratings['movie'].append(float(line[1]))
            ratings['rating'].append(float(line[2]))
            if float(line[0]) not in sparse['user']:
                sparse['user'].append(float(line[0]))  # available users
            if float(line[1]) not in sparse['movie']:
                sparse['movie'].append(float(line[1]))  # available movies
    sparisty = len(ratings['rating'])/(float((len(sparse['user'])) * len(sparse['movie'])))
    return ratings, sparisty


class Recommand:
    def __init__(self):
        self.get_data_matrix()

    def get_data_matrix(self):
        max_user_id = -1
        max_movie_id = -1

        filename = 'recommand/ml-latest-small/ratings.csv'
        with open(filename, "rt") as input:
            reader = csv.reader(input, delimiter=',', quoting=csv.QUOTE_NONE)
            next(reader, None)  # skip header
            for line in reader:
                user = int(line[0])
                movie = int(line[1])
                rating = float(line[2])

                if user > max_user_id:
                    max_user_id = user

                if movie > max_movie_id:
                    max_movie_id = movie

        self.max_movie_id = max_movie_id
        self.max_user_id = max_user_id

        max_user_id += 1
        max_movie_id += 1
        rating_matrix = np.array([[None] * max_movie_id] * max_user_id)
        print rating_matrix.shape
        with open(filename, "rt") as input:
            reader = csv.reader(input, delimiter=',', quoting=csv.QUOTE_NONE)
            next(reader, None)  # skip header
            for line in reader:
                user = int(line[0])
                movie = int(line[1])
                rating = float(line[2])

                rating_matrix[user][movie] = rating

        self.ratings_matrix = rating_matrix

    def preprocessing(self):  # q1-6
        self.ratings, self.sparisty = read_data()
        print 'sparisty: ' + str(self.sparisty)

        # Q2
        plot2_y = np.zeros(11)
        for i in range(len(self.ratings['rating'])):
            plot2_y[int(self.ratings['rating'][i] / 0.5)] += 1
        plt.bar(range(0, 11), plot2_y)
        plt.show()

        users, movies = set(), set()
        user_rating_num, movie_rating_num = defaultdict(int), defaultdict(int)
        movie_rating = defaultdict(list)

        for u in range(self.max_user_id + 1):
            for m in range(self.max_movie_id + 1):
                rating = self.ratings_matrix[u][m]
                if rating:
                    users.add(u)
                    movies.add(m)
                    user_rating_num[u] += 1
                    movie_rating_num[m] += 1
                    movie_rating[m].append(rating)

        # print len(users), len(movies)
        combinations = len(users) * len(movies)
        rating_num = 100004.0
        print "Sparisty = " + str(rating_num / combinations)    # Q1

        # Q3, Q4
        plot_freqency(movie_rating_num, 'Movie Rating Frequency')
        plot_freqency(user_rating_num, 'User Rating Frequency')

        # Q6
        movie_var = defaultdict(int)
        for ratings in movie_rating.values():
            movie_var[int(np.var(ratings) / 0.5)] += 1

        max_var = max(movie_var.keys())
        movie_var_list = [0] * (max_var + 1)
        for var, count in movie_var.items():
            movie_var_list[var] = count

        X = np.arange(len(movie_var_list))
        plt.bar(X, movie_var_list)
        plt.xticks(X, map(str, (np.arange(0, len(movie_var_list) / 2, 0.5))))
        plt.title('Variance of Movies')
        plt.show()
        
        # Q3 Q4?
        # movie_count = {}
        # for i in range (len(self.ratings['rating'])):
        #     key = int (self.ratings['movie'][i])
        #     if not key in movie_count.keys():
        #         movie_count[ self.ratings['movie'][i] ] = 0
        #     else:
        #         movie_count[ self.ratings['movie'][i] ] += 1
        # movie_rats = [(i, movie_count[i]) for i in movie_count]
        # movie_rats = sorted(movie_rats, cmp = lambda x, y: cmp(y[1], x[1]))
        # movie_plot = [i[1] for i in movie_rats]
        # plt.plot(movie_plot)
        # plt.show()

    def knn_run(self, folds=2, step_size=20, test_filter=None, threshold=2, msg=None):
        sim_options = {
            'name': 'pearson_baseline',
            'shrinkage': 0  # no shrinkage
        }

        rmse_by_k = []
        mae_by_k = []
        k_values = []
        for k in range(4, 101, step_size):
            k_values.append(k/2)
            algo = knns.KNNWithMeans(k=k/2, sim_options=sim_options)
            kf = KFold(n_splits=folds)
            rmse_by_fold = []
            mae_by_fold = []
            for trainset, testset in kf.split(self.data):
                algo.fit(trainset)
                if test_filter:
                    testset = test_filter(testset, threshold)
                predictions = algo.test(testset)
                rmse_by_fold.append(accuracy.rmse(predictions, verbose=True))
                mae_by_fold.append(accuracy.mae(predictions, verbose=True))
            rmse_by_k.append(np.mean(rmse_by_fold))
            mae_by_k.append(np.mean(mae_by_fold))

        plt.plot(k_values, rmse_by_k)
        plt.plot(k_values, mae_by_k)
        plt.legend(['RMSE', 'MAE'])
        plt.title(msg)
        plt.show()

    def knn(self):  # q7-11
        reader = Reader()
        # data = Dataset.load_from_file(filename, reader=reader )
        df = pd.DataFrame(self.ratings)
        self.data = Dataset.load_from_df(df[['user', 'movie', 'rating']], reader)

        # Q10, 12, 13, 14
        # self.knn_run(msg='not trimed')
        # self.knn_run(test_filter=self.trimPopular, msg='trimPopular')
        # self.knn_run(test_filter=self.trimUnpopular, msg='trimUnpopular')
        # self.knn_run(test_filter=self.trimHighVariance, msg='trimHighVariance')

        #Q15
        trainset, testset = train_test_split(self.data, test_size=0.1)
        threshold = [2.5,3.0,3.5,4.0]
        knn = knns.KNNWithMeans(k = 20, sim_options = {
            'name': 'pearson_baseline',
            'shrinkage': 0  # no shrinkage
        })
        knn.fit(trainset)
        pred = knn.test(testset)
        print "pred:",pred
        trueValue, scoreValue = [],[]
        for x in pred:
            trueValue.append(x[2]) #r_ui
            scoreValue.append(x[3]) #est

        for th in threshold:
            realValue = map(lambda x : 0 if x < th else 1, trueValue)
            # realValue = trueValue
            # for i in range(len(trueValue)):
            #     if trueValue[i]<th:
            #         realValue[i] = 0
            #     else:
            #         realValue[i] = 1
            # print realValue,scoreValue
            fpr, tpr, thresholds = roc_curve(realValue, scoreValue)
            roc_auc = auc(fpr, tpr)
            plt.plot(fpr, tpr, color='blue', linewidth=2.0, label='ROC (Area is %0.2f)' % roc_auc)
            plt.plot([0, 1], [0, 1], color='yellow', linewidth=2.0)
            plt.xlabel('FPR')
            plt.ylabel('TPR')
            plt.title('ROC with threshold = ' + str(th))
            plt.legend(loc="lower right")
            plt.show()
    def trimPopular(self, testset, threshold):
        df_testset = pd.DataFrame(testset, columns=['userId', 'movieId', 'rating'])
        counts = df_testset['movieId'].value_counts()
        df_trimmed_testset = df_testset[df_testset['movieId'].isin(counts[counts >= threshold].index)]
        return df_trimmed_testset.values.tolist()

    def trimUnpopular(self, testset, threshold):
        df_testset = pd.DataFrame(testset, columns=['userId', 'movieId', 'rating'])
        counts = df_testset['movieId'].value_counts()
        df_trimmed_testset = df_testset[df_testset['movieId'].isin(counts[counts <= threshold].index)]
        return df_trimmed_testset.values.tolist()

    def trimHighVariance(self, testset, minVariance):
        # print type(testset), len(testset)
        testsetTemp = self.trimPopular(testset, 5)
        dic = {}
        for (userID, movieID, rating) in testsetTemp:
            if (movieID in dic):
                dic[movieID].append(rating)
            else:
                dic[movieID] = [rating]
        for movieID in dic:
            if np.var(np.array(dic[movieID])) < minVariance:
                testsetTemp = filter(lambda x: x[1] != movieID, testsetTemp)  #(userID, movieID, rating), x[1] is movieID
        return testsetTemp

    def NMF_run(self, folds=2, step_size=20, test_filter=None, threshold=2, msg=None):
        rmse_by_k = []
        mae_by_k = []
        k_values = []
        for k in range(4, 101, step_size):
            k_values.append(k/2)
            algo = matrix_factorization.NMF(n_factors = k/2, biased= False)
            kf = KFold(n_splits=folds)
            rmse_by_fold = []
            mae_by_fold = []
            for trainset, testset in kf.split(self.data):
                algo.fit(trainset)
                if test_filter:
                    testset = test_filter(testset, threshold)
                predictions = algo.test(testset)
                rmse_by_fold.append(accuracy.rmse(predictions, verbose=True))
                mae_by_fold.append(accuracy.mae(predictions, verbose=True))
            rmse_by_k.append(np.mean(rmse_by_fold))
            mae_by_k.append(np.mean(mae_by_fold))
        
        plt.plot(k_values, rmse_by_k)
        plt.plot(k_values, mae_by_k)
        plt.legend(['RMSE', 'MAE'])
        plt.title(msg)
        plt.show()

    def NMF(self):
        reader = Reader()
        ratings, sparisty = read_data()
        df = pd.DataFrame(ratings)
        self.data = Dataset.load_from_df(df[['user', 'movie', 'rating']], reader)
        
        # Q17, 19, 20, 21
        # self.NMF_run(msg='not trimed')
        # self.NMF_run(test_filter=self.trimPopular, msg='trimPopular')
        # self.NMF_run(test_filter=self.trimUnpopular, msg='trimUnpopular')
        # self.NMF_run(test_filter=self.trimHighVariance, msg='trimHighVariance')

        # Q22
        trainset, testset = train_test_split(self.data, test_size=0.1)
        threshold = [2.5,3.0,3.5,4.0]
        nmf = matrix_factorization.NMF(20, biased= False)
        nmf.fit(trainset)
        pred = nmf.test(testset)
        print "pred:",pred
        trueValue, scoreValue = [],[]
        for x in pred:
            trueValue.append(x[2]) #r_ui
            scoreValue.append(x[3]) #est

        for th in threshold:
            realValue = map(lambda x : 0 if x < th else 1, trueValue)
            fpr, tpr, thresholds = roc_curve(realValue, scoreValue)
            roc_auc = auc(fpr, tpr)
            plt.plot(fpr, tpr, color='blue', linewidth=2.0, label='ROC (Area is %0.2f)' % roc_auc)
            plt.plot([0, 1], [0, 1], color='yellow', linewidth=2.0)
            plt.xlabel('FPR')
            plt.ylabel('TPR')
            plt.title('ROC with threshold = ' + str(th))
            plt.legend(loc="lower right")
            plt.show()

    def non_negative_matrix_factorization(self):
        factorization_model = NMF(n_components=20, init='nndsvda', random_state=0)
        U = factorization_model.fit_transform(self.ratings_matrix)
        V = factorization_model.components_
        print U
        print V
