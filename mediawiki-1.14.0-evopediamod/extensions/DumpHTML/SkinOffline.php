<?php

/**
 * Default skin for HTML dumps, based on MonoBook.php
 */

if( !defined( 'MEDIAWIKI' ) )
	die( 1 );

/**
 * Inherit main code from SkinTemplate, set the CSS and template filter.
 * @todo document
 * @addtogroup Skins
 */
class SkinOffline extends SkinTemplate {
	/** Using monobook. */
	function initPage( &$out ) {
		global $wgStylePath;
		SkinTemplate::initPage( $out );
		$this->template  = 'SkinOfflineTemplate';
		$this->skinpath = "$wgStylePath/offline";
	}

	function setupTemplate( $className, $repository = false, $cache_dir = false ) {
		global $wgFavicon;
		$tpl = parent::setupTemplate( $className, $repository, $cache_dir );
		$tpl->set( 'skinpath', $this->skinpath );
		$tpl->set( 'favicon', $wgFavicon );
		return $tpl;
	}

	function buildSidebar() {
		$sections = parent::buildSidebar();
		$badMessages = array( 'recentchanges-url', 'randompage-url' );
		$badUrls = array();
		foreach ( $badMessages as $msg ) {
			$badUrls[] = self::makeInternalOrExternalUrl( wfMsgForContent( $msg ) );
		}

		foreach ( $sections as $heading => $section ) {
			foreach ( $section as $index => $link ) {
				if ( in_array( $link['href'], $badUrls ) ) {
					unset( $sections[$heading][$index] );
				}
			}
		}
		return $sections;
	}

	function buildContentActionUrls() {
		global $wgHTMLDump;

		$content_actions = array();
		$nskey = $this->getNameSpaceKey();
		$content_actions[$nskey] = $this->tabAction(
			$this->mTitle->getSubjectPage(),
			$nskey,
			!$this->mTitle->isTalkPage() );

		$content_actions['talk'] = $this->tabAction(
			$this->mTitle->getTalkPage(),
			'talk',
			$this->mTitle->isTalkPage(),
			'',
			true);

		if ( isset( $wgHTMLDump ) ) {
			$content_actions['current'] = array(
				'text' => wfMsg( 'currentrev' ),
				'href' => str_replace( '$1', wfUrlencode( $this->mTitle->getPrefixedDBkey() ),
					$wgHTMLDump->oldArticlePath ),
				'class' => false
			);
		}
		return $content_actions;
	}

	function makeBrokenLinkObj( &$nt, $text = '', $query = '', $trail = '', $prefix = '' ) {
		if ( !isset( $nt ) ) {
			return "<!-- ERROR -->{$prefix}{$text}{$trail}";
		}

		if ( $nt->getNamespace() == NS_CATEGORY ) {
			# Determine if the category has any articles in it
			$dbr = wfGetDB( DB_SLAVE );
			$hasMembers = $dbr->selectField( 'categorylinks', '1', 
				array( 'cl_to' => $nt->getDBkey() ), __METHOD__ );
			if ( $hasMembers ) {
				return $this->makeKnownLinkObj( $nt, $text, $query, $trail, $prefix );
			}
		}

		if ( $text == '' ) {
			$text = $nt->getPrefixedText();
		}
		return $prefix . $text . $trail;
	}

	function printSource() {
		return '';
	}
}

/**
 * @todo document
 * @addtogroup Skins
 */
class SkinOfflineTemplate extends QuickTemplate {
	/**
	 * Template filter callback for MonoBook skin.
	 * Takes an associative array of data set from a SkinTemplate-based
	 * class, and a wrapper for MediaWiki's localization database, and
	 * outputs a formatted page.
	 *
	 * @private
	 */
        function execute() {
		wfSuppressWarnings();
?><h1 class="firstHeading"><?php $this->data['displaytitle']!=""?$this->html('title'):$this->text('title') ?></h1>
<div id="bodyContent">
<h3 id="siteSub"><?php $this->msg('tagline') ?></h3>
<div id="contentSub"><?php $this->html('subtitle') ?></div>
<?php $this->html('bodytext') ?>
<?php if($this->data['catlinks']) { ?><div id="catlinks"><?php       $this->html('catlinks') ?></div><?php } ?>
	    <div class="visualClear"></div>
</div>
<?php
		wfRestoreWarnings();
	}
}
?>
