import matplotlib.pyplot as plt

from utils import print_question, tokenizer, fetch_data, build_labels, new_line
from sklearn.feature_extraction.text import TfidfTransformer, CountVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.cluster import homogeneity_score, completeness_score, v_measure_score, adjusted_rand_score, adjusted_mutual_info_score
from sklearn.decomposition import TruncatedSVD, NMF
from sklearn.feature_extraction import text
from sklearn.metrics import confusion_matrix
from sklearn import preprocessing
from sklearn.preprocessing import FunctionTransformer
import numpy as np

stop_words = text.ENGLISH_STOP_WORDS
categories = [
    'comp.graphics',
    'comp.os.ms-windows.misc',
    'comp.sys.ibm.pc.hardware',
    'comp.sys.mac.hardware',
    'rec.autos',
    'rec.motorcycles',
    'rec.sport.baseball',
    'rec.sport.hockey'
]
allCat = [
    'comp.sys.ibm.pc.hardware',
    'comp.sys.mac.hardware',
    'misc.forsale',
    'soc.religion.christian',
    'comp.graphics',
    'comp.os.ms-windows.misc',
    'comp.windows.x',
    'rec.autos',
    'rec.motorcycles',
    'rec.sport.baseball',
    'rec.sport.hockey',
    'alt.atheism',
    'sci.crypt',
    'sci.electronics',
    'sci.med',
    'sci.space',
    'talk.politics.guns',
    'talk.politics.mideast',
    'talk.politics.misc',
    'talk.religion.misc'
]


def plot_res(data, all_r, name):
    keys = ['Homogeneity', 'Completeness', 'V-measure', 'RAND', 'Mutual']
    for key in keys:
        plt.plot(all_r, [res[key] for res in data], label=key)
        plt.xlabel('r value')
        plt.ylabel('value')
        plt.title(name)
        plt.legend(loc="best")
    plt.show()


class Clustering:
    def __init__(self):
        self.tfidf_transformer = TfidfTransformer()
        self.vectorizer = CountVectorizer(analyzer='word', stop_words=stop_words, min_df=3, tokenizer=tokenizer)
        self.svd = TruncatedSVD(n_components=1000, random_state=0)

        # build training data
        self.train_data = fetch_data(categories, 'train')
        self.train_labels = build_labels(self.train_data)
        self.vectors = self.to_vec(self.train_data.data)
        self.tfidf = self.to_tfidf(self.vectors)

        #build clustering required data
        self.lsip2 = TruncatedSVD(n_components=2, random_state=0)
        self.lsi_data = self.lsip2.fit_transform(self.tfidf)
        self.nmfp2 = NMF(n_components=2, init='random', random_state=0)
        self.nmf_data = self.nmfp2.fit_transform(self.tfidf)

    def _transform(self, data, tool):
        return tool.fit_transform(data)

    def to_vec(self, data):
        return self._transform(data, self.vectorizer)

    def to_tfidf(self, data):
        return self._transform(data, self.tfidf_transformer)

    def show_result(self, prediction, msg):
        new_line(50)
        print(msg)
        new_line(50)

        real = self.train_labels

        print "Confusion Matrix: "
        print str(confusion_matrix(real, prediction))

        homo_score = homogeneity_score(real, prediction)
        complete_score = completeness_score(real, prediction)
        v_score = v_measure_score(real, prediction)
        rand_score = adjusted_rand_score(real, prediction)
        mutual_info = adjusted_mutual_info_score(real, prediction)

        print("Homogeneity Score: %0.3f" % homo_score)
        print("Completeness Score: %0.3f" % complete_score)
        print("V-measure: %0.3f" % v_score)
        print("Adjusted Rand Score: %0.3f" % rand_score)
        print("Adjusted Mutual Info Score: %0.3f\n" % mutual_info)

        return {
            'Homogeneity': homo_score,
            'Completeness': complete_score,
            'V-measure': v_score,
            'RAND': rand_score,
            'Mutual': mutual_info
        }

    def q1(self):
        print_question('1')
        print "dimensions: ", self.tfidf.shape

    def q2(self):
        print_question('2')
        km = KMeans(n_clusters=2, max_iter=200, n_init=5)
        km.fit(self.tfidf)
        self.show_result(km.labels_, 'quesiton 2')

    def q3(self):
        print_question('3')

        # compaure variances
        svd = self.svd
        svd.fit(self.tfidf)
        variances = svd.explained_variance_ratio_.cumsum().tolist()
        plt.plot(range(1, 1001), variances, label="SVD")
        plt.xlabel('r')
        plt.ylabel('variance ratio')
        plt.title('variance ratio & r value relation')
        plt.show()

        # compare different r
        nmf_res = []
        svd_res = []
        all_r = [1, 2, 3, 5, 10, 20, 50, 100, 300]
        for r in all_r:
            km_svd = KMeans(n_clusters=2, max_iter=100, n_init=3)
            svd = TruncatedSVD(n_components=r, random_state=0)
            km_svd.fit(svd.fit_transform(self.tfidf))
            msg = 'svd with r=%s' % str(r)
            res_svd = self.show_result(km_svd.labels_, msg)

            km_nmf = KMeans(n_clusters=2, max_iter=100, n_init=3)
            nmf = NMF(n_components=r, init='random', random_state=0)
            km_nmf.fit(nmf.fit_transform(self.tfidf))
            msg = 'nmf with r=%s' % str(r)
            res_nmf = self.show_result(km_nmf.labels_, msg)

            nmf_res.append(res_nmf)
            svd_res.append(res_svd)

        plot_res(svd_res, all_r, 'SVD Result')
        plot_res(nmf_res, all_r, 'NMF Result')

    def q4helper(self, data, tag):
        km = KMeans(n_clusters=2, init='k-means++', max_iter=100, n_init=3)
        km.fit(data)
        centers = km.cluster_centers_
        plt.scatter(data[:,0], data[:,1], c=km.predict(data))
        plt.scatter(centers[:,0], centers[:,1], alpha=0.8, c="black") 
        plt.xlabel("x")
        plt.ylabel("y")
        plt.title(tag+" visualization")
        plt.show()

    def q4a(self):
        self.q4helper(self.lsi_data, "normal svd")
        self.q4helper(self.nmf_data, "normal nmf")

    def q4b1helper(self, data, tag):
        #Normalize
        data = preprocessing.scale(data, with_mean = False)
        # normalizer = Normalizer(copy=False)
        # lsa = make_pipeline(self.lsip2, normalizer)
        # data = lsa.fit_transform(self.lsi_data)
        # lsi_norm = 
        km = KMeans(n_clusters=2, init='k-means++', max_iter=100, n_init=3)
        km.fit(data)
        self.show_result(km.labels_, 'quesiton 4b1 with ' + tag)
        centers = km.cluster_centers_
        plt.scatter(data[:,0], data[:,1], c=km.predict(data))
        plt.scatter(centers[:,0], centers[:,1], alpha=0.8, c="black") 
        plt.xlabel("x")
        plt.ylabel("y")
        plt.title(tag + " visualization with normalization")
        plt.show()
        self.show_result(km.labels_, tag)

    def q4b1(self):
        self.q4b1helper(self.lsi_data, "normal svd")
        self.q4b1helper(self.nmf_data, "normal nmf")

    def q4b2(self):
        # Applying a non-linear transformation to the data vectors only after NMF. Here we use logarithm transformation as an example.
        data_nl_nmf = FunctionTransformer(np.log1p).transform(self.nmf_data)
        km = KMeans(n_clusters=2, init='k-means++', max_iter=100, n_init=3)
        km.fit(data_nl_nmf)
        self.show_result(km.labels_, 'non-linear transformation for nmf')
        centers = km.cluster_centers_
        plt.scatter(data_nl_nmf[:,0], data_nl_nmf[:,1], c=km.predict(data_nl_nmf))
        plt.scatter(centers[:,0], centers[:,1], alpha=0.8, c="black") 
        plt.xlabel("x")
        plt.ylabel("y")
        plt.title("visualization with non-linear transformation for nmf")
        plt.show()

    def q4b3(self):
        #Now try combining both transformations (in different orders) on NMF- reduced data.
        #1st non-linear and 2nd normalize:
        data_nl_nmf = FunctionTransformer(np.log1p).transform(self.nmf_data)
        data_combine = preprocessing.scale(data_nl_nmf, with_mean = False)
        km = KMeans(n_clusters=2, init='k-means++', max_iter=100, n_init=3)
        km.fit(data_combine)
        self.show_result(km.labels_, 'non-linear first and then normalization')
        centers = km.cluster_centers_
        plt.scatter(data_combine[:,0], data_combine[:,1], c=km.predict(data_combine))
        plt.scatter(centers[:,0], centers[:,1], alpha=0.8, c="black") 
        plt.xlabel("x")
        plt.ylabel("y")
        plt.title("Clustering Visualization with both transformation using non-linear first and then normalization")
        plt.show()

        #1st normalize and 2nd non-linear:
        data_normalize = preprocessing.scale(self.nmf_data, with_mean = False)
        data_combine = FunctionTransformer(np.log1p).transform(data_normalize)
        km = KMeans(n_clusters=2, init='k-means++', max_iter=100, n_init=3)
        km.fit(data_combine)
        self.show_result(km.labels_, 'normalization first and then non-linear')
        centers = km.cluster_centers_
        plt.scatter(data_combine[:,0], data_combine[:,1], c=km.predict(data_combine))
        plt.scatter(centers[:,0], centers[:,1], alpha=0.8, c="black") 
        plt.xlabel("x")
        plt.ylabel("y")
        plt.title("Clustering Visualization with both transformation using normalization first and then non-linear")
        plt.show()

    def q4(self):
        self.q4a()
        self.q4b1()
        self.q4b2()
        self.q4b3()


