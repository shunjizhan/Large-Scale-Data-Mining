#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import SGDClassifier
from sklearn.svm import LinearSVC
from sklearn.multiclass import OneVsOneClassifier, OneVsRestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_curve, auc
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
import pprint as pp
import datetime
import time
import pytz
import os
from sklearn import linear_model
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score


all_hashtags = {'gohawks', 'gopatriots', 'nfl', 'patriots', 'sb49', 'superbowl'}


def to_date(timestamp):
    pst_tz = pytz.timezone('US/Pacific')
    return datetime.datetime.fromtimestamp(timestamp, pst_tz)


def get_hours(data):
    return data.total_seconds() / 3600.0


def get_hour_diff(all_tweets):
    initDate = to_date(all_tweets[0]['firstpost_date']).replace(minute=0, second=0)
    endDate = to_date(all_tweets[-1]['firstpost_date'])
    return get_hours(endDate - initDate)


def get_location(location):
    keywords_0 = {'Washington', 'WA'}
    keywords_1 = {'Massachusetts', 'MA'}

    for word in keywords_0:
        if word in location:
            return 0

    for word in keywords_1:
        if word in location:
            return 1

    return -1


def init_and_last_time(data):
    return data[0]['firstpost_date'], data[-1]['firstpost_date']


def list_of_json_to_df(arr):
    # print len(arr)
    if (len(arr)==0):
        temp_dict = {
            'tweets_num': [0],
            'retweets_num': [0],
            'followers_num': [0],
            'followers_num_max': [0],
            'time_of_day': [0]
        }
        return pd.DataFrame(temp_dict), -1
    # df_superbowl = pd.DataFrame(arr)
    # df_new = pd.DataFrame(columns=['tweets_num','retweets_num','followers_num','followers_num_max','time_of_day'])
    initDate = to_date(arr[0]['firstpost_date']).replace(minute=0, second=0)
    hour_diff = get_hour_diff(arr)

    total_num_of_tweets = [0] * (int(hour_diff) + 1)
    total_num_of_retweets = [0] * (int(hour_diff) + 1)
    total_num_of_follower = [0] * (int(hour_diff) + 1)
    max_num_follower = [0] * (int(hour_diff) + 1)
    time_of_day = [0] * (int(hour_diff) + 1)

    for dta in arr:
        # new_entry = [1, 2, 3, 4, 5]
        # df_new.loc[len(df_new)] = new_entry
        # pass
        index = int(get_hours(to_date(dta['firstpost_date']) - initDate))
        # print index
        total_num_of_tweets[index] += 1
        total_num_of_retweets[index] += dta['metrics']['citations']['total']
        total_num_of_follower[index] += dta['author']['followers']
        max_num_follower[index] = max(max_num_follower[index], dta['author']['followers'])
        # time_of_day[index] = to_date(dta['firstpost_date']).hour
        time_of_day[0] = initDate.hour
        for i in range(1, len(time_of_day)):
            time_of_day[i] = (time_of_day[i-1] + 1) % 24

    data_dict = {
        'tweets_num': total_num_of_tweets,
        'retweets_num': total_num_of_retweets,
        'followers_num': total_num_of_follower,
        'followers_num_max': max_num_follower,
        'time_of_day': time_of_day
    }
    return pd.DataFrame(data_dict), initDate


def find_last_tweet(arr):
    last_time = -1
    last_tweet = None
    for tweet in arr:
        if int(tweet['firstpost_date']) > last_time:
            last_time = tweet['firstpost_date']
            last_tweet = tweet

    return last_tweet


class Prediction:
    def __init__(self):
        self.all_data = {}
        for hashtag in all_hashtags:
            self.all_data[hashtag] = self.read_tweet(hashtag)

        self.all_data['superbowl'] = self.read_tweet('superbowl')

    def get_combined_data(self):
        ordered_hashtags = ['gopatriots', 'gohawks', 'nfl', 'patriots', 'sb49', 'superbowl']
        combined_data = []
        for hashtag in ordered_hashtags:
            combined_data.extend(self.all_data[hashtag])

        big_six = map(lambda x: x[-1], self.all_data.values())
        combined_data.append(find_last_tweet(big_six))

        return combined_data

    def read_tweet(self, hashtag, max_line=3000):
        if hashtag not in all_hashtags:
            raise Exception('no such data!')

        if hashtag in self.all_data.keys():
            return self.all_data[hashtag]

        file = './tweet_data/tweets_#%s.txt' % hashtag
        tweets = []
        counter = 0
        for line in open(file, 'r'):
            data = json.loads(line)
            tweets.append(data)
            counter += 1
            if (max_line > 0 and counter > max_line):
                break

        self.all_data[hashtag] = tweets
        return tweets

    def plot_histogram(self, hashtag):
        all_tweets = self.read_tweet(hashtag)
        initDate = to_date(all_tweets[0]['firstpost_date']).replace(minute=0, second=0)
        hour_diff = get_hour_diff(all_tweets)
        X = range(0, int(hour_diff) + 1)
        Y = [0] * (int(hour_diff) + 1)
        for tweet in all_tweets:
            index = int(get_hours(to_date(tweet['firstpost_date']) - initDate))
            Y[index] += 1
        plt.bar(X, Y, width=1)
        plt.title('%s number of tweets per hour' % hashtag)
        plt.show()

    def new_df(self, old_df):
        new_dict = {
                'tweets_num': [old_df['tweets_num']],
                'retweets_num': [old_df['retweets_num']],
                'followers_num': [old_df['followers_num']],
                'followers_num_max': [old_df['followers_num_max']],
                'time_of_day': [old_df['time_of_day']]
                }
        new_df = pd.DataFrame(new_dict)
        return new_df

    def concat_data(self, data, target):
        new_data = pd.DataFrame([[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]])
        new_target = []
        entry_5_hours = []
        temp_entry = 0
        if not (len(data))==0:
            for i in range (0, len(data), 5):
                entry_5_hours = []
                entry_5_hours.append(self.new_df(data.iloc[i]))
                if i+1 < len(data):
                    entry_5_hours.append(self.new_df(data.iloc[i+1]))
                else:
                    entry_5_hours.append(pd.DataFrame([[0,0,0,0,0]]))
                if i+2 < len(data):
                    entry_5_hours.append(self.new_df(data.iloc[i+2]))
                else:
                    entry_5_hours.append(pd.DataFrame([[0,0,0,0,0]]))
                if i+3 < len(data):
                    entry_5_hours.append(self.new_df(data.iloc[i+3]))
                else:
                    entry_5_hours.append(pd.DataFrame([[0,0,0,0,0]]))
                if i+4 < len(data):
                    entry_5_hours.append(self.new_df(data.iloc[i+4]))
                else:
                    entry_5_hours.append(pd.DataFrame([[0,0,0,0,0]]))

                
                new_entry = (pd.concat(entry_5_hours, axis = 1, ignore_index=True))
                print new_entry
                print new_data
                new_data.append(new_entry)
                # print len(new_data)

                if i+5 < len(data):
                    new_target.append( data.iloc[i+5]['tweets_num'])
                else:
                    new_target.append( 0 )

        return new_data, new_target

    def train_3_models_aggregate(self):
        combined_data_list = self.get_combined_data()
        combined_data, initDate = list_of_json_to_df(combined_data_list)
        combined_target = list(combined_data['tweets_num'])
        combined_target.insert(0, 0)
        combined_target = combined_target[:-1]

        # split data into 3 groups
        combined_data_p1, combined_data_p2, combined_data_p3, combined_target_p1, combined_target_p2, combined_target_p3 = self.split_to_3(combined_data, combined_target, initDate)
        
        # need to concatenate the datas in to rows of 25 features
        concat_combined_data_p1, concat_combined_target_p1 = self.concat_data(combined_data_p1, combined_data_p2)

        # create 3 linear regression models
        m1 = linear_model.LinearRegression()
        m2 = linear_model.LinearRegression()
        m3 = linear_model.LinearRegression()
        # train the models
        m1.fit(concat_combined_data_p1, concat_combined_target_p1)
        if not len(combined_data_p2) == 0: 
            m2.fit(combined_data_p2, combined_target_p1)
        if not len(combined_data_p2) == 0:
            m3.fit(combined_data_p3, combined_target_p1)
        # return the trained models
        return m1, m2, m3

    # split passed-in data into 3 groups by before, between, or after Feb 01 8AM and Feb 01 8PM
    def split_to_3(self, data, target, initDate):
        tz = initDate.tzinfo
        dt = datetime.datetime(2015,2,1,8,tzinfo =tz)
        index_feb_1_8am = int(get_hours(dt - initDate))
        dt = datetime.datetime(2015,2,1,16, tzinfo =tz)
        index_feb_1_8pm = int(get_hours(dt - initDate))

        data_p1 = data[:index_feb_1_8am]
        data_p2 = data[index_feb_1_8am:index_feb_1_8pm]
        data_p3 = data[index_feb_1_8pm:]
        target_p1 = target[:index_feb_1_8am]
        target_p2 = target[index_feb_1_8am:index_feb_1_8pm]
        target_p3 = target[index_feb_1_8pm:]
        # return the splitted data
        return data_p1, data_p2, data_p3, target_p1, target_p2, target_p3


    def q1(self):
        all_tweets = self.read_tweet('gohawks')
        tweetsLen = len(all_tweets)
        hour_diff = get_hour_diff(all_tweets)
        print 'average tweets per hour: %.3f' % (tweetsLen / hour_diff)

        all_follower = 0.0
        all_retweets = 0.0
        for dta in all_tweets:
            all_follower += int(dta['author']['followers'])
            all_retweets += int(dta['metrics']['citations']['total'])

        print 'average followers of users: %.3f' % (all_follower / tweetsLen)
        print 'average number of retweets: %.3f' % (all_retweets / tweetsLen)

        self.plot_histogram('superbowl')
        self.plot_histogram('nfl')

    def map_hour(self, data):
        initTime = data['firstpost_date'][0]
        data['firstpost_date'] = data['firstpost_date'].apply (lambda x : get_hours(to_date(x) - to_date(initTime)))


    def linear_regression(self):
        data, initDate = list_of_json_to_df(self.all_data['superbowl'])

        target = list(data['tweets_num'])
        target.insert(0, 0)
        target = target[:-1]
        reg = linear_model.LinearRegression()
        reg.fit(data.as_matrix(), target)
        predict = reg.predict(data.as_matrix())
        train_errors = reg.score(data.as_matrix(), target)
        r2_sco = r2_score(target, predict)
        print 'Training Accuracy: ', train_errors, 'R Squared Score', r2_sco
        # print total_num_of_tweets
        # print total_num_of_follower
        # print time_of_day
        # print to_date(self.all_data['superbowl'][0]['firstpost_date'])
        # print df_new, 'dsad'

        # print self.all_data['superbowl'][0]['firstpost_date']
        # tz = to_date(self.all_data['superbowl'][0]['firstpost_date']).tzinfo
        # dt = datetime.datetime(2015,2,1,8,tzinfo =tz)
        # index_feb_1_8am = int(get_hours(dt - initDate))
        # dt = datetime.datetime(2015,2,1,16, tzinfo =tz)
        # index_feb_1_8pm = int(get_hours(dt - initDate))
        # data_I = data[:index_feb_1_8am]
        # data_II = data[index_feb_1_8am:index_feb_1_8pm]
        # data_III = data[index_feb_1_8pm:]
        # target_I = target[:index_feb_1_8am]
        # target_II = target[index_feb_1_8am:index_feb_1_8pm]
        # target_III = target[index_feb_1_8pm:]

        data_I, data_II, data_III, target_I, target_II, target_III = self.split_to_3(data, target, initDate)

        kf = KFold(n_splits=10)
        # window I
        errors_I_lm = []
        errors_I_ridge = []
        errors_I_lasso = []
        for train_index, test_index in kf.split(data_I):
            score1, score2, score3 = self.test_with_3_models(train_index, test_index, data_I, target_I)
            errors_I_lm.append(score1)
            errors_I_ridge.append(score2)
            errors_I_lasso.append(score3)
        print np.mean(errors_I_lm)
        print np.mean(errors_I_ridge)
        print np.mean(errors_I_lasso)

        # window II
        if len(data_II)==0:
            pass
        errors_II_lm = []
        errors_II_ridge = []
        errors_II_lasso = []
        for train_index, test_index in kf.split(data_II):
            score1, score2, score3 = self.test_with_3_models(train_index, test_index, data_II, target_II)
            errors_II_lm.append(score1)
            errors_II_ridge.append(score2)
            errors_II_lasso.append(score3)
        print np.mean(errors_II_lm)
        print np.mean(errors_II_ridge)
        print np.mean(errors_II_lasso)

        # window III
        if len(data_III)==0:
            pass
        errors_III_lm = []
        errors_III_ridge = []
        errors_III_lasso = []
        for train_index, test_index in kf.split(data_III):
            score1, score2, score3 = self.test_with_3_models(train_index, test_index, data_III, target_III)
            errors_III_lm.append(score1)
            errors_III_ridge.append(score2)
            errors_III_lasso.append(score3)
        print np.mean(errors_III_lm)
        print np.mean(errors_III_ridge)
        print np.mean(errors_III_lasso)

    def run_combined_data(self):
        combined_data_list = self.get_combined_data()
        combined_data, initDate = list_of_json_to_df(combined_data_list)
        combined_target = list(combined_data['tweets_num'])
        combined_target.insert(0, 0)
        combined_target = combined_target[:-1]

        print len(combined_data), len(combined_target)

        errors_I_lm = []
        errors_I_ridge = []
        errors_I_lasso = []
        kf = KFold(n_splits=10)
        for train_index, test_index in kf.split(combined_data):
            score1, score2, score3 = self.test_with_3_models(train_index, test_index, combined_data, combined_target)
            errors_I_lm.append(score1)
            errors_I_ridge.append(score2)
            errors_I_lasso.append(score3)
        print np.mean(errors_I_lm)
        print np.mean(errors_I_ridge)
        print np.mean(errors_I_lasso)

    def test_with_3_models(self, train_index, test_index, data, target):
        train_data = data.iloc[train_index]
        test_data = data.iloc[test_index]
        train_target = pd.DataFrame(target).iloc[train_index]
        test_target = pd.DataFrame(target).iloc[test_index]
        # linear regression
        lm = linear_model.LinearRegression()
        lm.fit(train_data.as_matrix(), train_target)
        predicted = lm.predict(test_data)
        score_lm = r2_score(predicted, test_target)
        # ridge
        r = linear_model.Ridge(alpha = 0.01)
        r.fit(train_data.as_matrix(), train_target)
        predicted = r.predict(test_data)
        score_r = r2_score(predicted, test_target)
        # lasso
        las = linear_model.Lasso(alpha = 0.01)
        las.fit(train_data.as_matrix(), train_target)
        predicted = las.predict(test_data)
        score_las = r2_score(predicted, test_target)

        return score_lm, score_r, score_las


    def q1_3(self):
        initDate = to_date(self.all_data['superbowl'][0]['firstpost_date']).replace(minute=0, second=0)
        hour_diff = get_hour_diff(self.all_data['superbowl'])
        total_num_of_tweets = [0] * (int(hour_diff) + 1)
        total_num_of_retweets = [0] * (int(hour_diff) + 1)
        total_num_of_follower = [0] * (int(hour_diff) + 1)
        max_num_follower = [0] * (int(hour_diff) + 1)
        time_of_day = [0] * (int(hour_diff) + 1)
        total_favourite_num = [0] * (int(hour_diff) + 1)
        for dta in self.all_data['superbowl']:
            index = int(get_hours(to_date(dta['firstpost_date']) - initDate))
            total_favourite_num[index] += dta['tweet']['user']['favourites_count']
            total_num_of_tweets[index] += 1
            total_num_of_retweets[index] += dta['metrics']['citations']['total']
            total_num_of_follower[index] += dta['author']['followers']
            # max_num_follower[index] = max(max_num_follower[index], dta['author']['followers'])
            time_of_day[index] = to_date(dta['firstpost_date']).hour
        time_of_day[0] = initDate.hour
        for i in range(1, len(time_of_day)):
            time_of_day[i] = (time_of_day[i-1] + 1) % 24

        data_dict = {
            'tweets_num': total_num_of_tweets,
            'retweets_num': total_num_of_retweets,
            'followers_num': total_num_of_follower,
            'favourite_num': total_favourite_num,
            'time_of_day': time_of_day
        }

        data_ = pd.DataFrame(data_dict)


        target = list(data_['tweets_num'])
        target.insert(0, 0)  # 412
        target = target[:-1] # 411
        reg = linear_model.LinearRegression()

        for feature in ['tweets_num','retweets_num','favourite_num']:
            data = data_[[feature]]
            reg.fit(data.as_matrix(), target)
            predict = reg.predict(data.as_matrix())
            train_errors = reg.score(data.as_matrix(), target)
            r2_sco = r2_score(target, predict)
            print 'Training Accuracy: ', train_errors, 'R Squared Score', r2_sco
            fig = plt.figure()
            ax1 = fig.add_subplot(111)
            # print len(self.all_data['superbowl']), len(target_), len(target)
            plt.plot((0,0), (1,1), linewidth=2.0)
            plt.ylabel("real # of tweets for next hour")
            plt.xlabel("predict # of tweets for next hour")
            plt.title("predictant versus value of tweets for next hour with feature: "+ feature)
            ax1.scatter(target, predict, s=3, c='b', marker="s", label='')
            plt.legend(loc='upper left');
            plt.show()

    def q1_5(self):
        # train 3 models
        m1, m2, m3 = self.train_3_models_aggregate()
        # model = m1
        m1 = 0
        m2 = 0
        m3 = 0

        path = './test_data/'
        for filename in os.listdir(path):
            print filename
            period = int(filename.split('period')[1][0])
            if period == 1:
                model = m1
            elif period == 2:
                model = m2
                continue
            elif period == 3:
                model = m3
                continue

            tweets = [[],[],[],[],[],[]]
            tweets_df = []
            with open(path+filename) as f:
                line = f.readline()
                first_data = json.loads(line)
                initDate = to_date(first_data['firstpost_date']).replace(minute=0, second=0)
            for line in open(path+filename, 'r'):
                data = json.loads(line)
                index = int(get_hours(to_date(data['firstpost_date']) - initDate))
                tweets[index].append(data)
            for i in range(0,5):
                tweets_df.append(list_of_json_to_df(tweets[i])[0])
                # temp_df = list_of_json_to_df(tweets[i])[0]
                # if not temp_df == None:
                    # tweets_df.append(list_of_json_to_df(tweets[i])[0])
            target = sum(list_of_json_to_df(tweets[5])[0]['tweets_num'].tolist())
            df_test = pd.concat(tweets_df, axis=1, ignore_index=True)
            df_target = target
            # print df_test,df_target
            # print tweets_df
            # print df_test
            # print df_target
            # pred = model.predict(df_test)
            # score = r2_score(pred, df_target)
            # print '='*60
            # print "The predicted total number of tweets in the next hour for the " + filename is str(pred)
            # print "The actual number is " + str(df_target)
            # print "The score is " + str(score)

    def part2(self):
        all_tweet = []
        labels = []
        for tweet in self.all_data['superbowl']:
            location = get_location(tweet['tweet']['user']['location'])
            content = tweet['tweet']['text']
            if location in {0, 1}:
                all_tweet.append(content)
                labels.append(location)

        count_vect = CountVectorizer()
        X_train_counts = count_vect.fit_transform(all_tweet)

        tfidf_transformer = TfidfTransformer()
        X_train_tfidf = tfidf_transformer.fit_transform(X_train_counts)

        # print X_train_tfidf.shape

        all_models = {
            'NB': MultinomialNB(),
            'SVM': LinearSVC(),
            'SGD': SGDClassifier(),
            'KNN': KNeighborsClassifier(),
            'TREE': DecisionTreeClassifier()
        }
        for name, model in all_models.items():
            # print type(pd.DataFrame(X_train_tfidf))
            self.location_predcition(X_train_tfidf, np.array(labels), model, name)

    def location_predcition(self, data, labels, model, name):
        kf = KFold(n_splits=5)
        real_labels, pred_labels = [], []
        for train_index, test_index in kf.split(data, labels):
            X_train, Y_train = data[train_index], labels[train_index]
            X_test, Y_test = data[test_index], labels[test_index]
            model.fit(X_train, Y_train)
            prediction = model.predict(X_test)

            pred_labels.extend(prediction)
            real_labels.extend(Y_test)

        acc = np.mean(pred_labels == real_labels)
        fpr, tpr, thresholds = roc_curve(real_labels, pred_labels)
        report = classification_report(real_labels, pred_labels, target_names=['WA', 'MA'])
        matrix = confusion_matrix(real_labels, pred_labels)
        roc_auc = auc(fpr, tpr)

        print "Accuracy: %.2f" % acc
        print "Classification Report:"
        print report
        print "Confusion Matrix:"
        print matrix

        plt.plot(fpr, tpr, color='blue', linewidth=2.0, label='ROC (Area is %0.2f)' % roc_auc)
        plt.plot([0, 1], [0, 1], color='yellow', linewidth=2.0)
        plt.xlabel('FPR')
        plt.ylabel('TPR')
        plt.title('ROC Curve with %s' % name)
        plt.legend(loc='best')
        plt.show()







